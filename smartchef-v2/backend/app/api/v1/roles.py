"""Role management API routes (dd-user-mgmt.md §9.3)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import success_response
from app.core.database import get_db
from app.core.security import require_capability
from app.schemas.role import CreateRoleRequest, UpdateRolePermissionsRequest, UpdateRoleRequest
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
@require_capability("role_manage")
async def list_roles(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.list_roles(db)
    return success_response(data)


@router.post("")
@require_capability("role_manage")
async def create_role(
    request: Request,
    body: CreateRoleRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.create_role(db, body.model_dump())
    return success_response(data, status_code=201)


@router.get("/{role_id}")
@require_capability("role_manage")
async def get_role(
    request: Request,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.get_role(db, role_id)
    return success_response(data)


@router.put("/{role_id}")
@require_capability("role_manage")
async def update_role(
    request: Request,
    role_id: UUID,
    body: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.update_role(db, role_id, body.model_dump(exclude_unset=True))
    return success_response(data)


@router.delete("/{role_id}")
@require_capability("role_manage")
async def delete_role(
    request: Request,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await role_service.delete_role(db, role_id)
    return success_response(None, msg="角色已删除")


@router.get("/{role_id}/permissions")
@require_capability("role_manage")
async def get_role_permissions(
    request: Request,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.get_role_permissions(db, role_id)
    return success_response(data)


@router.put("/{role_id}/permissions")
@require_capability("role_manage")
async def update_role_permissions(
    request: Request,
    role_id: UUID,
    body: UpdateRolePermissionsRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await role_service.update_role_permissions(db, role_id, body.permission_keys)
    return success_response(data)
