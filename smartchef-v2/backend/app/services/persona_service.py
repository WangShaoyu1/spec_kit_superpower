"""Persona CRUD service with mutual-exclusion activation."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.dialog_profile import DialogProfile, Persona
from app.schemas.profile import CreatePersonaRequest, UpdatePersonaRequest


async def list_personas(db: AsyncSession, profile_id: UUID) -> list[dict]:
    await _ensure_profile(db, profile_id)
    query = (
        select(Persona)
        .where(Persona.profile_id == profile_id)
        .order_by(Persona.is_active.desc(), Persona.created_at.desc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_to_dict(p) for p in rows]


async def create_persona(db: AsyncSession, profile_id: UUID, data: CreatePersonaRequest) -> dict:
    await _ensure_profile(db, profile_id)
    persona = Persona(
        profile_id=profile_id,
        name=data.name,
        system_prompt=data.system_prompt,
        personality=data.personality,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
    )
    db.add(persona)
    await db.flush()
    return _to_dict(persona)


async def get_persona(db: AsyncSession, persona_id: UUID) -> dict:
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise BusinessException("E40201", "人设不存在")
    return _to_dict(persona)


async def update_persona(db: AsyncSession, persona_id: UUID, data: UpdatePersonaRequest) -> dict:
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise BusinessException("E40201", "人设不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(persona, key, val)

    await db.flush()
    return _to_dict(persona)


async def delete_persona(db: AsyncSession, persona_id: UUID) -> None:
    persona = await db.get(Persona, persona_id)
    if not persona:
        raise BusinessException("E40201", "人设不存在")

    await db.delete(persona)
    await db.flush()


async def activate_persona(db: AsyncSession, profile_id: UUID, persona_id: UUID) -> dict:
    persona = await db.get(Persona, persona_id)
    if not persona or persona.profile_id != profile_id:
        raise BusinessException("E40201", "人设不存在")

    await db.execute(
        update(Persona)
        .where(Persona.profile_id == profile_id, Persona.is_active == True)  # noqa: E712
        .values(is_active=False)
    )

    persona.is_active = True
    await db.flush()
    return _to_dict(persona)


async def _ensure_profile(db: AsyncSession, profile_id: UUID) -> DialogProfile:
    profile = await db.get(DialogProfile, profile_id)
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")
    return profile


def _to_dict(p: Persona) -> dict:
    return {
        "id": str(p.id),
        "profile_id": str(p.profile_id),
        "name": p.name,
        "system_prompt": p.system_prompt,
        "personality": p.personality,
        "temperature": p.temperature,
        "max_tokens": p.max_tokens,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
