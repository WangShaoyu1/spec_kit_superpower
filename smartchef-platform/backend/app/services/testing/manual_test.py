"""手动单条对话测试服务：创建测试会话、发送消息、返回调试信息。"""
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis
from fastapi import HTTPException, status

from app.models.test_session import TestSession
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent, Slot, TrainingData
from app.services.nlu.pipeline import run_pipeline, PipelineConfig

__all__ = ["create_test_session", "send_message", "ManualTestChatResult"]


@dataclass
class ManualTestChatResult:
    """手动测试发送消息后的完整响应，含 debug_info。"""

    domain: str
    route_confidence: float
    intent: str | None
    intent_confidence: float | None
    slots: dict
    response_text: str
    needs_followup: bool
    language: str
    latency_ms: int
    debug_info: dict

    def to_dict(self) -> dict:
        """转换为 API 层可直接使用的字典。"""
        return {
            "domain": self.domain,
            "route_confidence": self.route_confidence,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "slots": self.slots,
            "response_text": self.response_text,
            "needs_followup": self.needs_followup,
            "language": self.language,
            "latency_ms": self.latency_ms,
            "debug_info": self.debug_info,
        }


async def create_test_session(
    db: AsyncSession,
    profile_id: UUID,
    name: str,
    device_context: dict | None = None,
    notes: str | None = None,
    created_by: UUID | None = None,
) -> TestSession:
    """创建测试会话，关联对话方案。"""
    result = await db.execute(select(DialogProfile).where(DialogProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话方案不存在")

    session = TestSession(
        name=name,
        profile_id=profile_id,
        device_context=device_context,
        notes=notes,
        created_by=created_by,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


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


async def send_message(
    db: AsyncSession,
    redis: aioredis.Redis,
    session_id: UUID,
    text: str,
) -> ManualTestChatResult:
    """发送消息到 NLU Pipeline，收集并返回调试信息（路由、意图、槽位、耗时等）。"""
    result = await db.execute(
        select(TestSession).where(TestSession.id == session_id)
    )
    test_session = result.scalar_one_or_none()
    if not test_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试会话不存在")

    result = await db.execute(
        select(DialogProfile).options(selectinload(DialogProfile.persona)).where(
            DialogProfile.id == test_session.profile_id
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话方案不存在")

    registered = await _load_registered_intents(db, profile)
    config = _build_pipeline_config(profile, registered)

    # 测试会话使用独立 device_id，会话之间相互隔离
    device_id = f"test_{test_session.id}"
    pipeline_result = await run_pipeline(
        db=db,
        redis=redis,
        text=text,
        device_id=device_id,
        device_context=test_session.device_context,
        config=config,
    )

    return ManualTestChatResult(
        domain=pipeline_result.domain,
        route_confidence=pipeline_result.route_confidence,
        intent=pipeline_result.intent,
        intent_confidence=pipeline_result.intent_confidence,
        slots=pipeline_result.slots,
        response_text=pipeline_result.response_text,
        needs_followup=pipeline_result.needs_followup,
        language=pipeline_result.language,
        latency_ms=pipeline_result.latency_ms,
        debug_info=pipeline_result.debug_info,
    )
