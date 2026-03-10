"""版本加载器：从 PublishedVersion 加载活跃版本配置到内存。

负责从数据库加载当前活跃的发布版本，缓存其关联的 DialogProfile、
意图配置、知识库引用等，供 NLU Pipeline 等运行时使用。
"""
import asyncio
import logging
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models.published_version import PublishedVersion
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent
from app.services.nlu.pipeline import PipelineConfig

logger = logging.getLogger(__name__)


@dataclass
class ActiveVersionConfig:
    """活跃版本的完整运行时配置，供 Pipeline 等消费。"""

    version_id: UUID
    version_tag: str
    profile_id: UUID
    pipeline_config: PipelineConfig

    def to_pipeline_config(self) -> PipelineConfig:
        """返回可直接传入 run_pipeline 的 PipelineConfig。"""
        return self.pipeline_config


def _build_pipeline_config(profile: DialogProfile, registered_intents: list[dict]) -> PipelineConfig:
    """根据对话方案和意图列表构建 PipelineConfig。"""
    persona_data = None
    if profile.persona:
        persona_data = {
            "name": profile.persona.name,
            "personality": profile.persona.personality,
            "tone_style": profile.persona.tone_style,
            "system_prompt": profile.persona.system_prompt,
        }
    return PipelineConfig(
        profile_id=profile.id,
        llm_provider=profile.llm_provider,
        llm_config=profile.llm_config or {},
        persona_data=persona_data,
        routing_strategy=profile.routing_strategy,
        session_timeout_minutes=profile.session_timeout_minutes,
        registered_intents=registered_intents,
        knowledge_base_ids=profile.knowledge_base_ids or [],
        has_knowledge_base=bool(profile.knowledge_base_ids),
    )


async def _load_registered_intents(db: AsyncSession, profile: DialogProfile) -> list[dict]:
    """加载对话方案关联的意图及其槽位、训练数据。"""
    profile_intent_ids = profile.intent_ids or []
    query = select(Intent).options(
        selectinload(Intent.slots),
        selectinload(Intent.training_data),
    )
    if profile_intent_ids:
        query = query.where(Intent.id.in_(profile_intent_ids))
    result = await db.execute(query)
    intents = result.scalars().unique().all()

    registered = []
    for intent in intents:
        registered.append({
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
        })
    return registered


# --- 内存缓存 ---
_cache: ActiveVersionConfig | None = None
_cache_lock = asyncio.Lock()


def get_active_version() -> ActiveVersionConfig | None:
    """返回当前缓存的活跃版本配置；若未加载则返回 None。

    同步方法，适用于已经通过 reload_version 预加载的场景。
    """
    return _cache


async def reload_version(db: AsyncSession | None = None) -> ActiveVersionConfig | None:
    """从数据库重新加载活跃版本配置并更新内存缓存。

    Args:
        db: 可选，传入已有 Session 时复用以支持事务；否则创建新 Session。

    Returns:
        加载成功返回 ActiveVersionConfig，无活跃版本或加载失败返回 None。
    """
    global _cache
    use_own_session = db is None

    async def _do_load(session: AsyncSession) -> ActiveVersionConfig | None:
        # 1. 加载当前活跃的 PublishedVersion
        result = await session.execute(
            select(PublishedVersion).where(PublishedVersion.is_active == True).limit(1)
        )
        version = result.scalar_one_or_none()
        if not version:
            logger.warning("无活跃的发布版本 (is_active=True)")
            return None

        # 2. 加载关联的 DialogProfile（含 Persona）
        profile_result = await session.execute(
            select(DialogProfile)
            .options(selectinload(DialogProfile.persona))
            .where(DialogProfile.id == version.profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            logger.error(f"活跃版本 {version.id} 关联的对话方案 {version.profile_id} 不存在")
            return None

        # 3. 加载意图配置（含槽位、训练数据）
        registered_intents = await _load_registered_intents(session, profile)

        # 4. 构建 PipelineConfig
        pipeline_config = _build_pipeline_config(profile, registered_intents)

        return ActiveVersionConfig(
            version_id=version.id,
            version_tag=version.version_tag,
            profile_id=profile.id,
            pipeline_config=pipeline_config,
        )

    try:
        if use_own_session:
            async with async_session_factory() as session:
                config = await _do_load(session)
        else:
            config = await _do_load(db)

        async with _cache_lock:
            _cache = config

        if config:
            logger.info(
                f"版本配置已刷新: version_id={config.version_id}, "
                f"version_tag={config.version_tag}, profile_id={config.profile_id}"
            )
        return config
    except Exception as e:
        logger.exception(f"加载活跃版本失败: {e}")
        return None


def clear_cache() -> None:
    """清空内存缓存。版本变更或需要强制刷新时可调用。"""
    global _cache
    _cache = None
    logger.info("版本配置缓存已清空")
