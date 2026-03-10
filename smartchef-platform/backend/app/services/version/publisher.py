"""版本发布服务：快照方案、切换活跃版本、清除设备会话。

实现 FR-015/FR-016：
- 将对话方案（指令+知识库+人设）打包为统一版本发布
- 版本发布后，所有设备立即切换到新版本，现有设备会话上下文重置
"""
import logging
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent
from app.models.published_version import PublishedVersion
from app.services.session.device_session import clear_all_sessions
from app.services.version.loader import reload_version

logger = logging.getLogger(__name__)


def _build_profile_snapshot(profile: DialogProfile) -> dict:
    """构建对话方案配置快照（供版本隔离使用）。"""
    return {
        "name": profile.name,
        "description": profile.description,
        "llm_provider": profile.llm_provider,
        "llm_config": profile.llm_config or {},
        "persona_id": str(profile.persona_id) if profile.persona_id else None,
        "routing_strategy": profile.routing_strategy,
        "session_timeout_minutes": profile.session_timeout_minutes,
        "intent_ids": [str(i) for i in (profile.intent_ids or [])],
        "knowledge_base_ids": [str(k) for k in (profile.knowledge_base_ids or [])],
        "status": profile.status,
    }


def _build_intent_snapshot(intents: list) -> list[dict]:
    """构建意图+槽位完整快照。"""
    result = []
    for intent in intents:
        item = {
            "intent_key": intent.intent_key,
            "display_name": intent.display_name,
            "category": intent.category,
            "slots": [
                {
                    "slot_key": s.slot_key,
                    "entity_type": s.entity_type,
                    "is_required": s.is_required,
                    "prompt_text": s.prompt_text,
                    "display_name": s.display_name,
                    "sort_order": s.sort_order,
                }
                for s in (intent.slots or [])
            ],
            "training_texts": [td.text for td in (intent.training_data or [])],
        }
        result.append(item)
    return result


async def _load_intents_for_profile(db: AsyncSession, profile: DialogProfile) -> list:
    """加载对话方案关联的意图（含槽位、训练数据）。"""
    profile_intent_ids = profile.intent_ids or []
    query = select(Intent).options(
        selectinload(Intent.slots),
        selectinload(Intent.training_data),
    )
    if profile_intent_ids:
        query = query.where(Intent.id.in_(profile_intent_ids))
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def clear_all_device_sessions(redis: aioredis.Redis) -> int:
    """通过 SCAN + DEL 清除 Redis 中所有设备会话。

    Key 格式: session:{device_id}
    """
    return await clear_all_sessions(redis)


async def _clear_sessions_safely(redis: aioredis.Redis, context: str) -> int:
    """清除设备会话，失败不阻塞发布流程。返回清除数量，失败时返回 0。"""
    try:
        cleared = await clear_all_device_sessions(redis)
        return cleared
    except Exception as e:
        logger.warning("清除设备会话失败(%s)，发布继续: %s", context, e, exc_info=True)
        return 0


async def publish_version(
    db: AsyncSession,
    redis: aioredis.Redis,
    profile_id: UUID,
    version_tag: str,
    *,
    description: str | None = None,
    published_by: UUID | None = None,
) -> PublishedVersion:
    """发布新版本：快照对话方案配置、创建 PublishedVersion、将旧版本置为 inactive。

    流程：
    1. 加载对话方案及关联意图，构建快照（逻辑层）
    2. 将所有旧版本 is_active 置为 False
    3. 创建新 PublishedVersion 记录，is_active=True
    4. 清除 Redis 中所有设备会话（SCAN + DEL）
    5. 刷新版本加载器缓存（reload_version）
    """
    # 1. 加载对话方案
    result = await db.execute(
        select(DialogProfile)
        .options(selectinload(DialogProfile.persona))
        .where(DialogProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise ValueError(f"对话方案不存在: {profile_id}")

    # 2. 快照对话方案配置（供版本隔离，当前模型无快照列时仅做逻辑层校验）
    profile_snapshot = _build_profile_snapshot(profile)
    intents = await _load_intents_for_profile(db, profile)
    intent_snapshot = _build_intent_snapshot(intents)
    logger.info(
        f"快照完成: profile={profile.name}, intents={len(intent_snapshot)}, "
        f"profile_snapshot_keys={list(profile_snapshot.keys())}"
    )

    # 3. 将旧版本置为 inactive
    await db.execute(
        update(PublishedVersion).where(PublishedVersion.is_active == True).values(is_active=False)
    )

    # 4. 创建新版本记录
    version = PublishedVersion(
        profile_id=profile_id,
        version_tag=version_tag,
        description=description,
        is_active=True,
        published_by=published_by,
    )
    db.add(version)
    await db.flush()

    # 5. 清除所有设备会话（失败不阻塞发布）
    cleared = await _clear_sessions_safely(redis, "publish_version")
    logger.info(f"发布版本 {version_tag}: 已清除 {cleared} 个设备会话")

    # 6. 刷新版本加载器缓存
    await reload_version(db)
    logger.info(f"版本加载器已刷新: version_id={version.id}")

    # 供扩展：若 PublishedVersion 增加 profile_snapshot/intent_snapshot 列，
    # 可将 profile_snapshot、intent_snapshot 写入版本记录
    return version


async def switch_active_version(
    db: AsyncSession,
    redis: aioredis.Redis,
    version_id: UUID,
) -> PublishedVersion:
    """切换活跃版本：将指定版本设为 active，旧版置 inactive，清除会话并刷新缓存。"""
    result = await db.execute(
        select(PublishedVersion).where(PublishedVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise ValueError(f"版本不存在: {version_id}")

    # 将当前活跃版本置为 inactive
    await db.execute(
        update(PublishedVersion).where(PublishedVersion.is_active == True).values(is_active=False)
    )
    version.is_active = True
    await db.flush()

    # 清除所有设备会话（失败不阻塞切换）
    cleared = await _clear_sessions_safely(redis, "switch_active_version")
    logger.info(f"切换活跃版本至 {version.version_tag}: 已清除 {cleared} 个设备会话")

    # 刷新版本加载器缓存
    await reload_version(db)
    return version


async def rollback_version(
    db: AsyncSession,
    redis: aioredis.Redis,
) -> PublishedVersion | None:
    """回滚到上一个版本：将当前 active 置为 inactive，激活按时间倒序的上一版本。

    按 created_at 降序排序，取第二个作为「上一版本」；若仅有一个版本则返回 None。
    """
    result = await db.execute(
        select(PublishedVersion)
        .order_by(PublishedVersion.created_at.desc())
        .limit(2)
    )
    versions = list(result.scalars().all())
    if len(versions) < 2:
        logger.warning("无上一版本可供回滚")
        return None

    previous = versions[1]
    target = previous

    # 先将所有版本置为 inactive，再激活目标版本
    await db.execute(
        update(PublishedVersion).where(PublishedVersion.is_active == True).values(is_active=False)
    )
    target.is_active = True
    await db.flush()

    # 清除所有设备会话（失败不阻塞回滚）
    cleared = await _clear_sessions_safely(redis, "rollback_version")
    logger.info(f"回滚至版本 {target.version_tag}: 已清除 {cleared} 个设备会话")

    await reload_version(db)
    return target
