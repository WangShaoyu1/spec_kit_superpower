import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DEBUG"] = "true"

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def _settings():
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture(scope="session")
async def _init_infrastructure(_settings):
    """Start real DB + Redis connections once per session."""
    from app.core.database import init_db, close_db
    from app.core.redis import init_redis, close_redis

    await init_db()
    try:
        await init_redis()
    except Exception:
        pass
    yield
    await close_db()
    try:
        await close_redis()
    except Exception:
        pass


@pytest.fixture
async def client(_init_infrastructure):
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def login_as_admin(client) -> dict:
    """Login as admin, clearing rate-limit keys first to avoid 429."""
    try:
        from app.core.redis import get_redis
        redis = get_redis()
        keys = await redis.keys("login_rate:*")
        if keys:
            await redis.delete(*keys)
    except RuntimeError:
        pass

    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123456"})
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["data"]
