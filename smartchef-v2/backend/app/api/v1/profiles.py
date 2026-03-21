"""Dialog Profile API routes — profile CRUD, persona management, library bindings."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import paginated_response, success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.schemas.profile import (
    CreatePersonaRequest,
    CreateProfileRequest,
    UpdateBindingsRequest,
    UpdatePersonaRequest,
    UpdateProfileRequest,
)
from app.services import binding_service, persona_service, profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------

@router.get("")
@require_capability("profile_read")
async def list_profiles(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items, total = await profile_service.list_profiles(
        db, page=page, page_size=page_size, search=search, status=status,
    )
    return paginated_response(items, total=total, page=page, page_size=page_size)


@router.get("/stats")
@require_capability("profile_read")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)):
    data = await profile_service.get_stats(db)
    return success_response(data)


@router.post("")
@require_capability("profile_write")
async def create_profile(
    request: Request,
    body: CreateProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await profile_service.create_profile(db, body, user.user_id)
    return success_response(data, status_code=201)


@router.get("/{profile_id}")
@require_capability("profile_read")
async def get_profile(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await profile_service.get_profile(db, profile_id)
    return success_response(data)


@router.put("/{profile_id}")
@require_capability("profile_write")
async def update_profile(
    request: Request,
    profile_id: UUID,
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await profile_service.update_profile(db, profile_id, body)
    return success_response(data)


@router.delete("/{profile_id}")
@require_capability("profile_write")
async def delete_profile(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await profile_service.delete_profile(db, profile_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

@router.get("/{profile_id}/personas")
@require_capability("profile_read")
async def list_personas(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await persona_service.list_personas(db, profile_id)
    return success_response(data)


@router.post("/{profile_id}/personas")
@require_capability("profile_write")
async def create_persona(
    request: Request,
    profile_id: UUID,
    body: CreatePersonaRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await persona_service.create_persona(db, profile_id, body)
    return success_response(data, status_code=201)


@router.put("/{profile_id}/personas/{persona_id}")
@require_capability("profile_write")
async def update_persona(
    request: Request,
    profile_id: UUID,
    persona_id: UUID,
    body: UpdatePersonaRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await persona_service.update_persona(db, persona_id, body)
    return success_response(data)


@router.delete("/{profile_id}/personas/{persona_id}")
@require_capability("profile_write")
async def delete_persona(
    request: Request,
    profile_id: UUID,
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await persona_service.delete_persona(db, persona_id)
    return success_response(None, msg="删除成功")


@router.post("/{profile_id}/personas/{persona_id}/activate")
@require_capability("profile_write")
async def activate_persona(
    request: Request,
    profile_id: UUID,
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await persona_service.activate_persona(db, profile_id, persona_id)
    return success_response(data)


# ---------------------------------------------------------------------------
# Library Bindings
# ---------------------------------------------------------------------------

@router.get("/{profile_id}/intent-libraries")
@require_capability("profile_read")
async def list_bindings(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await binding_service.list_bindings(db, profile_id)
    return success_response(data)


@router.put("/{profile_id}/intent-libraries")
@require_capability("profile_write")
async def sync_bindings(
    request: Request,
    profile_id: UUID,
    body: UpdateBindingsRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await binding_service.sync_bindings(db, profile_id, body.bindings)
    return success_response(data)
