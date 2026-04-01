from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import ROLE_CAPABILITIES
from app.dependencies import (
    ApiError,
    build_summary,
    create_audit_log,
    ensure_role_exists,
    ensure_status_exists,
    generate_temporary_password,
    get_db,
    load_capabilities,
    next_user_id,
    require_capability,
    response_envelope,
    serialize_user,
)
from app.models import CapabilityDefinition, UserAccount
from app.security import hash_password


router = APIRouter(prefix="/admin", tags=["user-mgmt"])


class CreateUserRequest(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,20}$")
    name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=64)
    role: str


class ChangeRoleRequest(BaseModel):
    role: str


class ChangeStatusRequest(BaseModel):
    status: str


@router.get("/users")
def list_users(
    request: Request,
    _: UserAccount = Depends(require_capability("user_manage")),
    session: Session = Depends(get_db),
):
    users = session.execute(select(UserAccount).order_by(UserAccount.created_at)).scalars().all()
    return response_envelope(
        request,
        data={
            "items": [serialize_user(user) for user in users],
            "summary": build_summary(users),
        },
    )


@router.post("/users")
def create_user(
    payload: CreateUserRequest,
    request: Request,
    actor: UserAccount = Depends(require_capability("user_manage")),
    session: Session = Depends(get_db),
):
    ensure_role_exists(payload.role)
    existing = session.execute(select(UserAccount).where(UserAccount.username == payload.username)).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "USER-409-USERNAME", "用户名已存在，请更换后重试")

    user = UserAccount(
        id=next_user_id(session),
        username=payload.username,
        display_name=payload.name,
        password_hash=hash_password(payload.password),
        role_key=payload.role,
        status="active",
        token_version=1,
        is_builtin_admin=False,
    )
    session.add(user)
    create_audit_log(session, actor.id, user.id, "user.created", {"role": payload.role})
    session.commit()
    session.refresh(user)
    return response_envelope(request, data={"user": serialize_user(user)})


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: ChangeRoleRequest,
    request: Request,
    actor: UserAccount = Depends(require_capability("user_manage")),
    session: Session = Depends(get_db),
):
    ensure_role_exists(payload.role)
    user = session.get(UserAccount, user_id)
    if user is None:
        raise ApiError(404, "USER-404-NOT-FOUND", "目标用户不存在")
    if user.is_builtin_admin and payload.role != "admin":
        raise ApiError(409, "USER-409-BUILTIN-ADMIN", "内置管理员账号受保护，不能执行该操作")

    current_admin_count = session.execute(
        select(func.count()).select_from(UserAccount).where(UserAccount.role_key == "admin", UserAccount.status == "active")
    ).scalar_one()
    if user.role_key == "admin" and payload.role != "admin" and current_admin_count <= 1:
        raise ApiError(409, "USER-409-LAST-ADMIN", "系统至少保留一个启用中的管理员账号")

    before_role = user.role_key
    user.role_key = payload.role
    user.token_version += 1
    create_audit_log(session, actor.id, user.id, "user.role_changed", {"before": before_role, "after": payload.role})
    session.commit()
    session.refresh(user)
    return response_envelope(request, data={"user": serialize_user(user), "capabilities": load_capabilities(session, user.role_key)})


@router.post("/users/{user_id}/status")
def set_user_status(
    user_id: str,
    payload: ChangeStatusRequest,
    request: Request,
    actor: UserAccount = Depends(require_capability("user_manage")),
    session: Session = Depends(get_db),
):
    ensure_status_exists(payload.status)
    user = session.get(UserAccount, user_id)
    if user is None:
        raise ApiError(404, "USER-404-NOT-FOUND", "目标用户不存在")
    if user.username == "admin" or user.is_builtin_admin:
        raise ApiError(409, "USER-409-BUILTIN-ADMIN", "内置管理员账号受保护，不能执行该操作")

    current_admin_count = session.execute(
        select(func.count()).select_from(UserAccount).where(UserAccount.role_key == "admin", UserAccount.status == "active")
    ).scalar_one()
    if payload.status == "disabled" and user.role_key == "admin" and user.status == "active" and current_admin_count <= 1:
        raise ApiError(409, "USER-409-LAST-ADMIN", "系统至少保留一个启用中的管理员账号")

    before_status = user.status
    user.status = payload.status
    user.token_version += 1
    create_audit_log(session, actor.id, user.id, "status_changed", {"before": before_status, "after": payload.status})
    session.commit()
    session.refresh(user)
    return response_envelope(request, data={"user": serialize_user(user)})


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: str,
    request: Request,
    actor: UserAccount = Depends(require_capability("user_manage")),
    session: Session = Depends(get_db),
):
    user = session.get(UserAccount, user_id)
    if user is None:
        raise ApiError(404, "USER-404-NOT-FOUND", "目标用户不存在")

    temporary_password = generate_temporary_password()
    user.password_hash = hash_password(temporary_password)
    user.token_version += 1
    create_audit_log(
        session,
        actor.id,
        user.id,
        "password_reset",
        {"password_reset": True, "delivery": "out_of_band", "require_password_change": True},
    )
    session.commit()
    return response_envelope(
        request,
        data={"password_reset": True, "delivery": "out_of_band", "require_password_change": True},
    )


@router.get("/permission-matrix")
def permission_matrix(
    request: Request,
    _: UserAccount = Depends(require_capability("user_manage")),
    session: Session = Depends(get_db),
):
    capability_defs = session.execute(select(CapabilityDefinition).order_by(CapabilityDefinition.capability_key)).scalars().all()
    matrix = []
    for item in capability_defs:
        matrix.append(
            {
                "capability_key": item.capability_key,
                "description": item.description,
                "admin": item.capability_key in ROLE_CAPABILITIES["admin"],
                "pm": ROLE_CAPABILITIES["pm"].get(item.capability_key),
                "tester": item.capability_key in ROLE_CAPABILITIES["tester"],
            }
        )
    return response_envelope(request, data={"items": matrix})
