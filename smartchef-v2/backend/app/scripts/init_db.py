"""T014: Seed data script — admin user + 3 default roles + 21 capability points (dd-global.md §7)."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session_factory, init_db
from app.core.security import hash_password
from app.models.user import Permission, Role, RolePermission, User

PERMISSIONS = [
    # 指令库域
    ("intent_library_read", "查看指令库", "指令库"),
    ("intent_library_write", "编辑指令库", "指令库"),
    ("intent_library_delete", "删除指令库", "指令库"),
    ("model_train", "训练模型", "指令库"),
    ("model_evaluate", "评估模型", "指令库"),
    ("model_test", "测试模型", "指令库"),
    ("model_publish", "发布模型", "指令库"),
    ("model_download", "下载模型", "指令库"),
    # 对话方案域
    ("profile_read", "查看对话方案", "对话方案"),
    ("profile_write", "编辑对话方案", "对话方案"),
    ("profile_publish", "发布方案版本", "对话方案"),
    # 知识库域
    ("knowledge_read", "查看知识库", "知识库"),
    ("knowledge_write", "编辑知识库", "知识库"),
    # 批量测试域
    ("batch_test_read", "查看批量测试", "批量测试"),
    ("batch_test_write", "执行批量测试", "批量测试"),
    # 监控域
    ("monitoring_read", "查看监控数据", "监控"),
    ("monitoring_manage", "管理告警规则", "监控"),
    # 系统域
    ("user_manage", "管理用户", "系统"),
    ("role_manage", "管理角色", "系统"),
    ("version_read", "查看版本", "系统"),
    ("system_config", "系统配置", "系统"),
]

ROLES = {
    "admin": {"description": "系统管理员", "builtin": True, "permissions": "all"},
    "pm": {
        "description": "产品经理",
        "builtin": True,
        "permissions": [
            "intent_library_read", "intent_library_write", "intent_library_delete",
            "model_train", "model_evaluate", "model_test", "model_publish", "model_download",
            "profile_read", "profile_write", "profile_publish",
            "knowledge_read", "knowledge_write",
            "batch_test_read", "batch_test_write",
            "monitoring_read",
            "version_read",
        ],
    },
    "tester": {
        "description": "测试工程师",
        "builtin": True,
        "permissions": [
            "intent_library_read",
            "model_test",
            "profile_read",
            "knowledge_read",
            "batch_test_read", "batch_test_write",
            "monitoring_read",
            "version_read",
        ],
    },
}


async def seed(db: AsyncSession):
    """Idempotent seed: skip if data already exists."""
    existing = await db.execute(select(Permission).limit(1))
    if existing.scalar_one_or_none():
        print("Seed data already exists, skipping.")
        return

    perm_map: dict[str, Permission] = {}
    for key, label, module in PERMISSIONS:
        p = Permission(id=uuid.uuid4(), key=key, label=label, module=module)
        db.add(p)
        perm_map[key] = p
    await db.flush()

    role_map: dict[str, Role] = {}
    for name, cfg in ROLES.items():
        role = Role(id=uuid.uuid4(), name=name, description=cfg["description"], is_builtin=cfg["builtin"])
        db.add(role)
        role_map[name] = role
    await db.flush()

    for name, cfg in ROLES.items():
        role = role_map[name]
        perms = perm_map.values() if cfg["permissions"] == "all" else [perm_map[k] for k in cfg["permissions"]]
        for p in perms:
            db.add(RolePermission(role_id=role.id, permission_id=p.id))
    await db.flush()

    settings = get_settings()
    admin_role = role_map["admin"]
    admin_user = User(
        id=uuid.uuid4(),
        username=settings.ADMIN_USERNAME,
        name="系统管理员",
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role_id=admin_role.id,
        status="active",
        is_builtin=True,
    )
    db.add(admin_user)
    await db.commit()

    print(f"Seed complete: {len(PERMISSIONS)} permissions, {len(ROLES)} roles, 1 admin user.")


async def main():
    await init_db()
    from app.core.database import async_session_factory as factory

    async with factory() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
