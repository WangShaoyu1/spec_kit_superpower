"""Role management CRUD service (dd-user-mgmt.md §9.3)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.models.user import Permission, Role, RolePermission, User


ALL_PERMISSION_KEYS: list[str] = [
    "intent_lib_view", "intent_lib_edit",
    "intent_manage", "intent_training_data_edit",
    "model_train", "model_evaluate", "model_publish",
    "profile_view", "profile_edit", "profile_publish",
    "knowledge_view", "knowledge_edit",
    "batch_test_run", "batch_test_view",
    "monitoring_view", "monitoring_alert_edit",
    "version_view", "version_publish",
    "user_manage", "role_manage",
    "system_settings",
]

PERMISSION_MODULES: dict[str, list[str]] = {
    "指令库": [
        "intent_lib_view", "intent_lib_edit",
        "intent_manage", "intent_training_data_edit",
        "model_train", "model_evaluate", "model_publish",
    ],
    "对话方案": ["profile_view", "profile_edit", "profile_publish"],
    "知识库": ["knowledge_view", "knowledge_edit"],
    "批量测试": ["batch_test_run", "batch_test_view"],
    "监控": ["monitoring_view", "monitoring_alert_edit"],
    "版本管理": ["version_view", "version_publish"],
    "系统": ["user_manage", "role_manage", "system_settings"],
}


async def list_roles(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Role)
        .options(
            selectinload(Role.users),
            selectinload(Role.role_permissions),
        )
        .order_by(Role.is_builtin.desc(), Role.created_at.asc())
    )
    roles = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "is_builtin": r.is_builtin,
            "user_count": len(r.users),
            "permission_count": len(r.role_permissions),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in roles
    ]


async def create_role(db: AsyncSession, data: dict) -> dict:
    existing = await db.execute(select(Role).where(Role.name == data["name"]))
    if existing.scalar_one_or_none():
        raise BusinessException("E10301", "角色名称已存在", http_status=409)

    permission_keys = data.get("permission_keys", [])
    await _validate_permission_keys(db, permission_keys)

    role = Role(name=data["name"], description=data.get("description"))
    db.add(role)
    await db.flush()

    if permission_keys:
        await _set_role_permissions(db, role.id, permission_keys)

    await db.refresh(role, attribute_names=["id", "created_at"])

    return {
        "id": str(role.id),
        "name": role.name,
        "description": role.description,
        "is_builtin": role.is_builtin,
        "permission_count": len(permission_keys),
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }


async def get_role(db: AsyncSession, role_id: UUID) -> dict:
    role = await db.get(
        Role, role_id,
        options=[selectinload(Role.role_permissions).selectinload(RolePermission.permission)],
    )
    if not role:
        raise BusinessException("E10302", "角色不存在", http_status=404)

    permissions = [rp.permission.key for rp in role.role_permissions]

    return {
        "id": str(role.id),
        "name": role.name,
        "description": role.description,
        "is_builtin": role.is_builtin,
        "permissions": permissions,
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }


async def update_role(db: AsyncSession, role_id: UUID, data: dict) -> dict:
    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException("E10302", "角色不存在", http_status=404)

    if role.is_builtin and "name" in data and data["name"] != role.name:
        raise BusinessException("E10303", "内置角色名称不可修改", http_status=403)

    if "name" in data and data["name"] is not None:
        dup = await db.execute(
            select(Role).where(Role.name == data["name"], Role.id != role_id)
        )
        if dup.scalar_one_or_none():
            raise BusinessException("E10301", "角色名称已存在", http_status=409)
        role.name = data["name"]

    if "description" in data:
        role.description = data["description"]

    await db.flush()

    return {
        "id": str(role.id),
        "name": role.name,
        "description": role.description,
        "is_builtin": role.is_builtin,
    }


async def delete_role(db: AsyncSession, role_id: UUID) -> None:
    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException("E10302", "角色不存在", http_status=404)

    if role.is_builtin:
        raise BusinessException("E10303", "内置角色不可删除", http_status=403)

    user_count = (
        await db.execute(
            select(func.count()).select_from(User).where(User.role_id == role_id)
        )
    ).scalar() or 0
    if user_count > 0:
        raise BusinessException("E10304", f"角色下仍有 {user_count} 个用户，不可删除", http_status=400)

    await db.delete(role)
    await db.flush()


async def get_role_permissions(db: AsyncSession, role_id: UUID) -> list[str]:
    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException("E10302", "角色不存在", http_status=404)

    result = await db.execute(
        select(Permission.key)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == role_id)
    )
    return list(result.scalars().all())


async def update_role_permissions(
    db: AsyncSession, role_id: UUID, permission_keys: list[str]
) -> list[str]:
    role = await db.get(Role, role_id)
    if not role:
        raise BusinessException("E10302", "角色不存在", http_status=404)

    await _validate_permission_keys(db, permission_keys)
    await _set_role_permissions(db, role_id, permission_keys)

    return permission_keys


async def get_all_permissions(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Permission).order_by(Permission.module, Permission.key))
    perms = result.scalars().all()

    modules: dict[str, list[dict]] = {}
    for p in perms:
        modules.setdefault(p.module, []).append({
            "key": p.key,
            "label": p.label,
        })

    return [
        {"module": module, "permissions": items}
        for module, items in modules.items()
    ]


async def _validate_permission_keys(db: AsyncSession, keys: list[str]) -> None:
    if not keys:
        return
    result = await db.execute(select(Permission.key).where(Permission.key.in_(keys)))
    valid = set(result.scalars().all())
    invalid = set(keys) - valid
    if invalid:
        raise BusinessException(
            "E10305",
            f"无效的权限标识: {', '.join(sorted(invalid))}",
            http_status=400,
        )


async def _set_role_permissions(
    db: AsyncSession, role_id: UUID, permission_keys: list[str]
) -> None:
    await db.execute(
        RolePermission.__table__.delete().where(RolePermission.role_id == role_id)
    )

    if not permission_keys:
        await db.flush()
        return

    result = await db.execute(
        select(Permission).where(Permission.key.in_(permission_keys))
    )
    perms = result.scalars().all()

    for perm in perms:
        db.add(RolePermission(role_id=role_id, permission_id=perm.id))

    await db.flush()
