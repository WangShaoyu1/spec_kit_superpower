import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, Role

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/smartchef_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_role(db_session):
    role = Role(
        name="管理员",
        permissions={
            "intent_management": {"read": True, "write": True, "delete": True},
            "knowledge_management": {"read": True, "write": True, "delete": True},
            "dialog_profile": {"read": True, "write": True, "delete": True},
            "testing": {"manual": True, "batch": True},
            "test_debug": {"read": True, "write": True},
            "version_publish": True,
            "monitoring": {"dashboard": True, "device_logs": True, "alerts": True},
            "user_management": True,
            "data_management": True,
        },
        is_system=True,
    )
    db_session.add(role)
    await db_session.flush()
    return role


@pytest.fixture
async def admin_user(db_session, admin_role):
    user = User(
        username="testadmin",
        password_hash=hash_password("test123456"),
        display_name="测试管理员",
        role_id=admin_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def admin_token(admin_user):
    return create_access_token(data={"sub": str(admin_user.id), "username": admin_user.username})


@pytest.fixture
async def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
