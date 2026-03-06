from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import require_permission
from app.schemas.test import TestSessionCreate, TestSessionInfo, TestChatRequest, TestChatResponse
from app.models.test_session import TestSession
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent, Slot, TrainingData
from app.services.nlu.pipeline import run_pipeline, PipelineConfig

router = APIRouter(prefix="/test", tags=["手动测试"])


@router.get("/sessions", response_model=list[TestSessionInfo])
async def list_test_sessions(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    result = await db.execute(select(TestSession).order_by(TestSession.created_at.desc()).limit(50))
    return [TestSessionInfo.model_validate(s) for s in result.scalars().all()]


@router.post("/sessions", response_model=TestSessionInfo, status_code=201)
async def create_test_session(
    body: TestSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("test_debug.write")),
):
    result = await db.execute(select(DialogProfile).where(DialogProfile.id == body.profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="对话方案不存在")

    session = TestSession(
        name=body.name, profile_id=body.profile_id,
        device_context=body.device_context, notes=body.notes,
        created_by=current_user.id,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return TestSessionInfo.model_validate(session)


@router.post("/chat", response_model=TestChatResponse)
async def test_chat(
    body: TestChatRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(require_permission("test_debug.write")),
):
    result = await db.execute(
        select(TestSession).where(TestSession.id == body.session_id)
    )
    test_session = result.scalar_one_or_none()
    if not test_session:
        raise HTTPException(status_code=404, detail="测试会话不存在")

    result = await db.execute(
        select(DialogProfile).where(DialogProfile.id == test_session.profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="对话方案不存在")

    intents_result = await db.execute(
        select(Intent).options(
            selectinload(Intent.slots),
            selectinload(Intent.training_data),
        )
    )
    intents = intents_result.scalars().unique().all()

    registered = []
    for intent in intents:
        registered.append({
            "intent_key": intent.intent_key,
            "display_name": intent.display_name,
            "category": intent.category,
            "slots": [
                {"slot_key": s.slot_key, "entity_type": s.entity_type,
                 "is_required": s.is_required, "prompt_text": s.prompt_text,
                 "display_name": s.display_name, "sort_order": s.sort_order}
                for s in (intent.slots or [])
            ],
            "training_texts": [td.text for td in (intent.training_data or [])],
        })

    persona_data = None
    if profile.persona:
        persona_data = {
            "name": profile.persona.name,
            "personality": profile.persona.personality,
            "tone_style": profile.persona.tone_style,
            "system_prompt": profile.persona.system_prompt,
        }

    config = PipelineConfig(
        profile_id=profile.id,
        llm_provider=profile.llm_provider,
        llm_config=profile.llm_config or {},
        persona_data=persona_data,
        routing_strategy=profile.routing_strategy,
        session_timeout_minutes=profile.session_timeout_minutes,
        registered_intents=registered,
        knowledge_base_ids=profile.knowledge_base_ids or [],
        has_knowledge_base=bool(profile.knowledge_base_ids),
    )

    device_id = f"test_{test_session.id}"
    pipeline_result = await run_pipeline(
        db=db, redis=redis, text=body.text,
        device_id=device_id, device_context=test_session.device_context,
        config=config,
    )

    return TestChatResponse(
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
