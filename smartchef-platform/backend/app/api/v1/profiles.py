from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.schemas.profile import (
    DialogProfileCreate, DialogProfileInfo, DialogProfileUpdate,
    PersonaCreate, PersonaInfo, PersonaUpdate,
)
from app.services import profile_service

router = APIRouter(prefix="/profiles", tags=["对话方案管理"])


@router.get("", response_model=list[DialogProfileInfo])
async def list_profiles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.read")),
):
    profiles = await profile_service.list_profiles(db)
    return [DialogProfileInfo.model_validate(p) for p in profiles]


@router.post("", response_model=DialogProfileInfo, status_code=201)
async def create_profile(
    body: DialogProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("dialog_profile.write")),
):
    profile = await profile_service.create_profile(db, body, current_user.id)
    return DialogProfileInfo.model_validate(profile)


@router.get("/{profile_id}", response_model=DialogProfileInfo)
async def get_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.read")),
):
    profile = await profile_service.get_profile(db, profile_id)
    return DialogProfileInfo.model_validate(profile)


@router.patch("/{profile_id}", response_model=DialogProfileInfo)
async def update_profile(
    profile_id: UUID, body: DialogProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.write")),
):
    profile = await profile_service.update_profile(db, profile_id, body)
    return DialogProfileInfo.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.delete")),
):
    await profile_service.delete_profile(db, profile_id)


# --- Persona endpoints ---

@router.get("/personas/list", response_model=list[PersonaInfo])
async def list_personas(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.read")),
):
    personas = await profile_service.list_personas(db)
    return [PersonaInfo.model_validate(p) for p in personas]


@router.post("/personas", response_model=PersonaInfo, status_code=201)
async def create_persona(
    body: PersonaCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.write")),
):
    persona = await profile_service.create_persona(db, body)
    return PersonaInfo.model_validate(persona)


@router.patch("/personas/{persona_id}", response_model=PersonaInfo)
async def update_persona(
    persona_id: UUID, body: PersonaUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.write")),
):
    persona = await profile_service.update_persona(db, persona_id, body)
    return PersonaInfo.model_validate(persona)


@router.delete("/personas/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("dialog_profile.delete")),
):
    await profile_service.delete_persona(db, persona_id)
