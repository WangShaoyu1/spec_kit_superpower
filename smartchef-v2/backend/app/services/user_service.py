"""User management CRUD service (dd-user-mgmt.md §9.2)."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.core.security import hash_password
from app.models.user import Permission, Role, RolePermission, User


async def list_users(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
) -> dict:
    base = select(User).options(selectinload(User.role))

    if search:
        pattern = f"%{search}%"
        base = base.where(or_(User.username.ilike(pattern), User.name.ilike(pattern)))
    if status:
        base = base.where(User.status == status)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows = (
        await db.execute(
            base.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    items = [
        {
            "id": str(u.id),
            "username": u.username,
            "name": u.name,
            "status": u.status,
            "is_builtin": u.is_builtin,
            "role": {"id": str(u.role.id), "name": u.role.name} if u.role else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in rows
    ]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def create_user(db: AsyncSession, data: dict) -> dict:
    existing = await db.execute(select(User).where(User.username == data["username"]))
    if existing.scalar_one_or_none():
        raise BusinessException("E10201", "用户名已存在", http_status=409)

    role = await db.get(Role, UUID(data["role_id"]))
    if not role:
        raise BusinessException("E10206", "指定的角色不存在", http_status=400)

    password_hash = hash_password(data["password"])

    user = User(
        username=data["username"],
        name=data["name"],
        password_hash=password_hash,
        role_id=role.id,
        status="active",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, attribute_names=["id", "created_at"])

    return {
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "status": user.status,
        "role": {"id": str(role.id), "name": role.name},
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


async def get_user(db: AsyncSession, user_id: UUID) -> dict:
    user = await db.get(User, user_id, options=[selectinload(User.role)])
    if not user:
        raise BusinessException("E10202", "用户不存在", http_status=404)

    permissions = await _load_permissions(db, user.role_id)

    return {
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "status": user.status,
        "is_builtin": user.is_builtin,
        "role": {"id": str(user.role.id), "name": user.role.name} if user.role else None,
        "capabilities": [p.key for p in permissions],
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


async def update_user(db: AsyncSession, user_id: UUID, data: dict) -> dict:
    user = await db.get(User, user_id, options=[selectinload(User.role)])
    if not user:
        raise BusinessException("E10202", "用户不存在", http_status=404)

    if user.is_builtin and data.get("status") == "disabled":
        raise BusinessException("E10203", "内置管理员账号不可禁用", http_status=403)

    if data.get("status") == "disabled":
        active_admins = await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.status == "active", User.id != user_id)
        )
        if (active_admins.scalar() or 0) == 0:
            raise BusinessException("E10204", "至少保留一个活跃用户", http_status=400)

    if "name" in data and data["name"] is not None:
        user.name = data["name"]
    if "status" in data and data["status"] is not None:
        user.status = data["status"]

    await db.flush()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "status": user.status,
        "role": {"id": str(user.role.id), "name": user.role.name} if user.role else None,
    }


async def delete_user(db: AsyncSession, user_id: UUID) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException("E10202", "用户不存在", http_status=404)

    if user.is_builtin:
        raise BusinessException("E10203", "内置管理员账号不可删除", http_status=403)

    if user.status != "disabled":
        raise BusinessException("E10204", "只能删除已禁用的用户", http_status=400)

    await db.delete(user)
    await db.flush()


async def reset_password(db: AsyncSession, user_id: UUID, new_password: str) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException("E10202", "用户不存在", http_status=404)

    user.password_hash = hash_password(new_password)
    await db.flush()


async def assign_role(db: AsyncSession, user_id: UUID, role_id: UUID) -> dict:
    user = await db.get(User, user_id)
    if not user:
        raise BusinessException("E10202", "用户不存在", http_status=404)

    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException("E10206", "指定的角色不存在", http_status=400)

    user.role_id = role.id
    await db.flush()

    return {
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "role": {"id": str(role.id), "name": role.name},
    }


async def _load_permissions(db: AsyncSession, role_id) -> list[Permission]:
    result = await db.execute(
        select(Permission)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == role_id)
    )
    return list(result.scalars().all())
