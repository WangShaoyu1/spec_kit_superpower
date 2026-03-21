"""Contract-test fixtures — httpx AsyncClient backed by mocked infrastructure."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import get_settings
from app.core.database import get_db
from app.main import create_app


def make_auth_header(capabilities: list[str] | None = None) -> dict[str, str]:
    """Build an Authorization header carrying a valid JWT with *capabilities*."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    caps = capabilities if capabilities is not None else [
        "user_manage", "role_manage", "intent_library_read", "intent_library_write",
        "intent_library_delete", "profile_read", "profile_write", "profile_publish",
        "knowledge_read", "knowledge_write", "batch_test_read", "batch_test_write",
        "batch_test_execute", "monitor_read", "alert_manage",
    ]
    payload = {
        "sub": str(uuid.uuid4()),
        "jti": str(uuid.uuid4()),
        "role_id": str(uuid.uuid4()),
        "capabilities": caps,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


async def _mock_get_db():
    yield AsyncMock()


@pytest.fixture
def app():
    application = create_app()
    application.dependency_overrides[get_db] = _mock_get_db
    return application


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
