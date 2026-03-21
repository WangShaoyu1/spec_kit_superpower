"""T007: RBAC require_capability middleware unit tests.

Tests for the capability-based permission check decorator.
Written before implementation (TDD Red phase).
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from jose import jwt

from app.core.config import get_settings


def _make_token(capabilities: list[str], expired: bool = False) -> str:
    """Helper: create a JWT with given capabilities."""
    import uuid
    from datetime import datetime, timedelta, timezone

    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "jti": str(uuid.uuid4()),
        "role_id": str(uuid.uuid4()),
        "capabilities": capabilities,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=-1 if expired else 1)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.asyncio
async def test_user_with_matching_capability_passes():
    from app.core.security import require_capability

    token = _make_token(["intent_library_read"])

    @require_capability("intent_library_read")
    async def handler(request):
        return {"status": "ok"}

    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.state = MagicMock()

    result = await handler(request)
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_user_missing_capability_returns_403():
    from app.core.security import require_capability

    token = _make_token(["intent_library_read"])

    @require_capability("user_manage")
    async def handler(request):
        return {"status": "ok"}

    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.state = MagicMock()

    with pytest.raises(Exception) as exc_info:
        await handler(request)
    assert "403" in str(exc_info.value) or "E10107" in str(exc_info.value)


@pytest.mark.asyncio
async def test_require_all_partial_capabilities_fails():
    from app.core.security import require_capability

    token = _make_token(["intent_library_read"])

    @require_capability("intent_library_read", "intent_library_write", require_all=True)
    async def handler(request):
        return {"status": "ok"}

    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.state = MagicMock()

    with pytest.raises(Exception):
        await handler(request)


@pytest.mark.asyncio
async def test_require_any_one_capability_passes():
    from app.core.security import require_capability

    token = _make_token(["intent_library_read"])

    @require_capability("intent_library_read", "user_manage", require_all=False)
    async def handler(request):
        return {"status": "ok"}

    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.state = MagicMock()

    result = await handler(request)
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_no_token_returns_401():
    from app.core.security import require_capability

    @require_capability("intent_library_read")
    async def handler(request):
        return {"status": "ok"}

    request = MagicMock()
    request.headers = {}
    request.state = MagicMock()

    with pytest.raises(Exception) as exc_info:
        await handler(request)
    assert "401" in str(exc_info.value) or "E10102" in str(exc_info.value)


@pytest.mark.asyncio
async def test_expired_token_returns_401():
    from app.core.security import require_capability

    token = _make_token(["intent_library_read"], expired=True)

    @require_capability("intent_library_read")
    async def handler(request):
        return {"status": "ok"}

    request = MagicMock()
    request.headers = {"Authorization": f"Bearer {token}"}
    request.state = MagicMock()

    with pytest.raises(Exception):
        await handler(request)
