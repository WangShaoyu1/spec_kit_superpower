"""User management API routes (dd-user-mgmt.md §9.2)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import paginated_response, success_response
from app.core.database import get_db
from app.core.security import require_capability
from app.schemas.role import AssignRoleRequest
from app.schemas.user import CreateUserRequest, ResetPasswordRequest, UpdateUserRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
@require_capability("user_manage")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status: str | None = Query(None, pattern=r"^(active|disabled)$"),
    db: AsyncSession = Depends(get_db),
):
    data = await user_service.list_users(
        db, page=page, page_size=page_size, search=search, status=status
    )
    return paginated_response(
        data["items"], total=data["total"], page=data["page"], page_size=data["page_size"]
    )


@router.post("")
@require_capability("user_manage")
async def create_user(
    request: Request,
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await user_service.create_user(db, body.model_dump())
    return success_response(data, status_code=201)


@router.get("/{user_id}")
@require_capability("user_manage")
async def get_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await user_service.get_user(db, user_id)
    return success_response(data)


@router.put("/{user_id}")
@require_capability("user_manage")
async def update_user(
    request: Request,
    user_id: UUID,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await user_service.update_user(db, user_id, body.model_dump(exclude_unset=True))
    return success_response(data)


@router.delete("/{user_id}")
@require_capability("user_manage")
async def delete_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await user_service.delete_user(db, user_id)
    return success_response(None, msg="用户已删除")


@router.put("/{user_id}/roles")
@require_capability("user_manage")
async def assign_role(
    request: Request,
    user_id: UUID,
    body: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await user_service.assign_role(db, user_id, UUID(body.role_id))
    return success_response(data)


@router.put("/{user_id}/password")
@require_capability("user_manage")
async def reset_password(
    request: Request,
    user_id: UUID,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    await user_service.reset_password(db, user_id, body.password)
    return success_response(None, msg="密码已重置")
