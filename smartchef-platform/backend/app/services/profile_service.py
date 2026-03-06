from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.dialog_profile import DialogProfile
from app.models.persona import Persona
from app.schemas.profile import (
    DialogProfileCreate, DialogProfileUpdate,
    PersonaCreate, PersonaUpdate,
)


async def list_profiles(db: AsyncSession) -> list[DialogProfile]:
    result = await db.execute(
        select(DialogProfile).options(selectinload(DialogProfile.persona)).order_by(DialogProfile.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def get_profile(db: AsyncSession, profile_id: UUID) -> DialogProfile:
    result = await db.execute(
        select(DialogProfile).options(selectinload(DialogProfile.persona)).where(DialogProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话方案不存在")
    return profile


async def create_profile(db: AsyncSession, data: DialogProfileCreate, user_id: UUID | None = None) -> DialogProfile:
    profile = DialogProfile(
        **data.model_dump(),
        created_by=user_id,
    )
    db.add(profile)
    await db.flush()
    return await get_profile(db, profile.id)


async def update_profile(db: AsyncSession, profile_id: UUID, data: DialogProfileUpdate) -> DialogProfile:
    profile = await get_profile(db, profile_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.flush()
    return await get_profile(db, profile_id)


async def delete_profile(db: AsyncSession, profile_id: UUID) -> None:
    profile = await get_profile(db, profile_id)
    await db.delete(profile)
    await db.flush()


# --- Persona operations ---

async def list_personas(db: AsyncSession) -> list[Persona]:
    result = await db.execute(select(Persona).order_by(Persona.created_at.desc()))
    return list(result.scalars().all())


async def get_persona(db: AsyncSession, persona_id: UUID) -> Persona:
    result = await db.execute(select(Persona).where(Persona.id == persona_id))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="人设不存在")
    return persona


async def create_persona(db: AsyncSession, data: PersonaCreate) -> Persona:
    persona = Persona(**data.model_dump())
    db.add(persona)
    await db.flush()
    await db.refresh(persona)
    return persona


async def update_persona(db: AsyncSession, persona_id: UUID, data: PersonaUpdate) -> Persona:
    persona = await get_persona(db, persona_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(persona, key, value)
    await db.flush()
    await db.refresh(persona)
    return persona


async def delete_persona(db: AsyncSession, persona_id: UUID) -> None:
    persona = await get_persona(db, persona_id)
    await db.delete(persona)
    await db.flush()
