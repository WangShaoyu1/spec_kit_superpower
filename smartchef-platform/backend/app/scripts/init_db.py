"""Initialize database with default admin account and system roles."""
import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory, engine, Base
from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User, Role

settings = get_settings()

DEFAULT_ADMIN_PERMISSIONS = {
    "intent_management": {"read": True, "write": True, "delete": True},
    "knowledge_management": {"read": True, "write": True, "delete": True},
    "dialog_profile": {"read": True, "write": True, "delete": True},
    "testing": {"manual": True, "batch": True},
    "version_publish": True,
    "monitoring": {"dashboard": True, "device_logs": True, "alerts": True},
    "user_management": True,
}

EDITOR_PERMISSIONS = {
    "intent_management": {"read": True, "write": True, "delete": False},
    "knowledge_management": {"read": True, "write": True, "delete": False},
    "dialog_profile": {"read": True, "write": True, "delete": False},
    "testing": {"manual": True, "batch": True},
    "version_publish": False,
    "monitoring": {"dashboard": True, "device_logs": True, "alerts": False},
    "user_management": False,
}

VIEWER_PERMISSIONS = {
    "intent_management": {"read": True, "write": False, "delete": False},
    "knowledge_management": {"read": True, "write": False, "delete": False},
    "dialog_profile": {"read": True, "write": False, "delete": False},
    "testing": {"manual": True, "batch": False},
    "version_publish": False,
    "monitoring": {"dashboard": True, "device_logs": False, "alerts": False},
    "user_management": False,
}


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        admin_role = (await session.execute(
            select(Role).where(Role.name == "管理员")
        )).scalar_one_or_none()

        if not admin_role:
            admin_role = Role(name="管理员", permissions=DEFAULT_ADMIN_PERMISSIONS, is_system=True)
            editor_role = Role(name="编辑员", permissions=EDITOR_PERMISSIONS, is_system=True)
            viewer_role = Role(name="查看者", permissions=VIEWER_PERMISSIONS, is_system=True)
            session.add_all([admin_role, editor_role, viewer_role])
            await session.flush()

        admin_user = (await session.execute(
            select(User).where(User.username == settings.ADMIN_USERNAME)
        )).scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                display_name="系统管理员",
                role_id=admin_role.id,
                is_active=True,
            )
            session.add(admin_user)

        await session.commit()
        print(f"Database initialized. Admin user: {settings.ADMIN_USERNAME}")


if __name__ == "__main__":
    asyncio.run(init_db())
