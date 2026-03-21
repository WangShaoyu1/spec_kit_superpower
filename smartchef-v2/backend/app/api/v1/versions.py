"""Published version API routes — publish, list, detail, archive."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import success_response
from app.core.database import get_db
from app.core.security import require_capability
from app.services import publisher_service

router = APIRouter(tags=["versions"])


@router.post("/profiles/{profile_id}/publish")
@require_capability("profile_publish")
async def publish(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await publisher_service.publish(db, profile_id, user.user_id)
    return success_response(data, status_code=201)


@router.get("/profiles/{profile_id}/versions")
@require_capability("profile_read")
async def list_versions(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await publisher_service.list_versions(db, profile_id)
    return success_response(data)


@router.get("/versions/{version_id}")
@require_capability("profile_read")
async def get_version(
    request: Request,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await publisher_service.get_version(db, version_id)
    return success_response(data)


@router.post("/versions/{version_id}/archive")
@require_capability("profile_publish")
async def archive_version(
    request: Request,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await publisher_service.archive_version(db, version_id)
    return success_response(data)
