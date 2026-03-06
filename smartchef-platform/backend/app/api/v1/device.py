"""Device-facing API: high-concurrency, device-isolated sessions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.device import DeviceDialogRequest, DeviceDialogResponse
from app.models.published_version import PublishedVersion
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent
from app.services.nlu.pipeline import run_pipeline, PipelineConfig
from app.services.session.device_session import delete_session

router = APIRouter(prefix="/dialog", tags=["设备端 API"])

_profile_cache: dict = {}


async def _get_active_profile(db: AsyncSession) -> DialogProfile:
    result = await db.execute(
        select(PublishedVersion).where(PublishedVersion.is_active == True).limit(1)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=503, detail="无已发布的对话方案版本")

    result = await db.execute(
        select(DialogProfile).where(DialogProfile.id == version.profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=503, detail="对话方案配置不存在")
    return profile


async def _build_pipeline_config(db: AsyncSession, profile: DialogProfile) -> PipelineConfig:
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

    return PipelineConfig(
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


@router.post("/chat", response_model=DeviceDialogResponse)
async def device_chat(
    body: DeviceDialogRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    profile = await _get_active_profile(db)
    config = await _build_pipeline_config(db, profile)

    device_context = body.device_context.model_dump() if body.device_context else None

    result = await run_pipeline(
        db=db, redis=redis, text=body.text,
        device_id=body.device_id, device_context=device_context,
        config=config,
    )

    return DeviceDialogResponse(
        domain=result.domain,
        intent=result.intent,
        slots=result.slots,
        response_text=result.response_text,
        needs_followup=result.needs_followup,
        session_id=result.session_id,
    )


@router.post("/reset")
async def reset_session(
    device_id: str,
    redis: aioredis.Redis = Depends(get_redis),
):
    await delete_session(redis, device_id)
    return {"status": "ok", "message": f"设备 {device_id} 会话已重置"}


@router.get("/version")
async def get_active_version(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PublishedVersion).where(PublishedVersion.is_active == True).limit(1)
    )
    version = result.scalar_one_or_none()
    if not version:
        return {"active": False, "version_tag": None}
    return {
        "active": True,
        "version_tag": version.version_tag,
        "profile_id": str(version.profile_id),
    }
