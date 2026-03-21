"""Permissions API — list all capabilities grouped by module."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import success_response
from app.core.database import get_db
from app.core.security import require_capability
from app.services import role_service

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("")
@require_capability("role_manage")
async def list_permissions(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.get_all_permissions(db)
    return success_response(data)
