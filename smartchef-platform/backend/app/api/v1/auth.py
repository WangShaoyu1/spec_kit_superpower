from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.schemas.user import (
    TokenRequest, TokenResponse,
    UserCreate, UserInfo,
    RoleCreate, RoleUpdate, RoleInfo,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证与用户管理"])


@router.post("/login", response_model=TokenResponse)
async def login(body: TokenRequest, db: AsyncSession = Depends(get_db)):
    token = await auth_service.login(db, body.username, body.password)
    return TokenResponse(access_token=token)


@router.get("/users", response_model=list[UserInfo])
async def get_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user_management")),
):
    users = await auth_service.list_users(db)
    return [
        UserInfo(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            role_id=u.role_id,
            role_name=u.role.name if u.role else None,
            permissions=u.role.permissions if u.role else None,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]


@router.post("/users", response_model=UserInfo, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user_management")),
):
    user = await auth_service.create_user(db, body)
    return UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role_id=user.role_id,
        role_name=user.role.name if user.role else None,
        permissions=user.role.permissions if user.role else None,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user=Depends(get_current_user)):
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        role_id=current_user.role_id,
        role_name=current_user.role.name if current_user.role else None,
        permissions=current_user.role.permissions if current_user.role else None,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.get("/roles", response_model=list[RoleInfo])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    roles = await auth_service.list_roles(db)
    return [RoleInfo.model_validate(r) for r in roles]


@router.post("/roles", response_model=RoleInfo, status_code=201)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user_management")),
):
    role = await auth_service.create_role(db, body.name, body.permissions)
    return RoleInfo.model_validate(role)


@router.patch("/roles/{role_id}", response_model=RoleInfo)
async def update_role(
    role_id: UUID,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user_management")),
):
    role = await auth_service.update_role(
        db, role_id, name=body.name, permissions=body.permissions
    )
    return RoleInfo.model_validate(role)
