"""T016: Authentication service (dd-user-mgmt.md §7 full login flow)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import AuthException
from app.core.rate_limiter import check_login_rate_limit, clear_login_failures, record_login_failure
from app.core.security import (
    generate_tokens,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from app.models.user import Permission, Role, RolePermission, User


async def login(db: AsyncSession, username: str, password: str, ip: str) -> dict:
    await check_login_rate_limit(ip, username)

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        await record_login_failure(username)
        raise AuthException("E10101", "用户名或密码错误", http_status=401)

    if not verify_password(password, user.password_hash):
        await record_login_failure(username)
        raise AuthException("E10101", "用户名或密码错误", http_status=401)

    if user.status == "disabled":
        raise AuthException("E10103", "账号已被禁用，请联系管理员", http_status=403)

    permissions = await _load_permissions(db, user.role_id)
    role = await db.get(Role, user.role_id)

    tokens = generate_tokens(user, permissions)

    await clear_login_failures(username)

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        **tokens,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "name": user.name,
            "role": {"id": str(role.id), "name": role.name},
            "capabilities": [p.key for p in permissions],
        },
    }


async def get_current_user(db: AsyncSession, payload: dict) -> dict:
    user = await db.get(User, payload["sub"])
    if not user:
        raise AuthException("E10202", "用户不存在", http_status=404)

    role = await db.get(Role, user.role_id)
    permissions = await _load_permissions(db, user.role_id)

    return {
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "role": {"id": str(role.id), "name": role.name},
        "capabilities": [p.key for p in permissions],
    }


async def refresh_token(db: AsyncSession, refresh_token_str: str) -> dict:
    payload = verify_refresh_token(refresh_token_str)

    user = await db.get(User, payload["sub"])
    if not user:
        raise AuthException("E10202", "用户不存在", http_status=404)
    if user.status == "disabled":
        raise AuthException("E10103", "账号已被禁用，请联系管理员", http_status=403)

    permissions = await _load_permissions(db, user.role_id)
    tokens = generate_tokens(user, permissions)

    return {
        "access_token": tokens["access_token"],
        "expires_in": tokens["expires_in"],
    }


async def _load_permissions(db: AsyncSession, role_id) -> list[Permission]:
    result = await db.execute(
        select(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == role_id)
    )
    return list(result.scalars().all())
