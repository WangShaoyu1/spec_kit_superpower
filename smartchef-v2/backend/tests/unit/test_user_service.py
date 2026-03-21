"""Unit tests for app.services.user_service — mock-based, no real DB."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.services import user_service


def _make_role(*, role_id=None, name="operator"):
    role = MagicMock()
    role.id = role_id or uuid4()
    role.name = name
    return role


def _make_user(*, user_id=None, username="alice", name="Alice", status="active",
               is_builtin=False, role=None):
    user = MagicMock()
    user.id = user_id or uuid4()
    user.username = username
    user.name = name
    user.status = status
    user.is_builtin = is_builtin
    user.role_id = (role or _make_role()).id
    user.role = role or _make_role()
    user.password_hash = "hashed"
    user.last_login_at = None
    now = datetime.now(timezone.utc)
    user.created_at = now
    user.updated_at = now
    return user


@pytest.mark.asyncio
@patch("app.services.user_service.hash_password", return_value="$2b$hashed")
async def test_create_user_success(mock_hash):
    db = AsyncMock(spec=AsyncSession)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=exec_result)

    role = _make_role(name="admin")
    db.get = AsyncMock(return_value=role)

    async def fake_refresh(obj, **kwargs):
        obj.id = uuid4()
        obj.created_at = datetime.now(timezone.utc)

    db.refresh = AsyncMock(side_effect=fake_refresh)

    data = {"username": "newuser", "name": "New User", "password": "Valid1234", "role_id": str(role.id)}
    result = await user_service.create_user(db, data)

    assert result["username"] == "newuser"
    assert result["role"]["name"] == "admin"
    db.add.assert_called_once()
    db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_create_user_duplicate_username():
    db = AsyncMock(spec=AsyncSession)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = _make_user(username="dup")
    db.execute = AsyncMock(return_value=exec_result)

    data = {"username": "dup", "name": "Dup", "password": "Valid1234", "role_id": str(uuid4())}
    with pytest.raises(BusinessException) as exc_info:
        await user_service.create_user(db, data)
    assert exc_info.value.error_code == "E10201"


@pytest.mark.asyncio
@patch("app.services.user_service.hash_password", return_value="$2b$hashed")
async def test_create_user_invalid_role(mock_hash):
    db = AsyncMock(spec=AsyncSession)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=exec_result)
    db.get = AsyncMock(return_value=None)

    data = {"username": "newuser", "name": "New", "password": "Valid1234", "role_id": str(uuid4())}
    with pytest.raises(BusinessException) as exc_info:
        await user_service.create_user(db, data)
    assert exc_info.value.error_code == "E10206"


@pytest.mark.asyncio
async def test_get_user_not_found():
    db = AsyncMock(spec=AsyncSession)
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.get_user(db, uuid4())
    assert exc_info.value.error_code == "E10202"


@pytest.mark.asyncio
async def test_update_user_builtin_cannot_disable():
    db = AsyncMock(spec=AsyncSession)
    user = _make_user(is_builtin=True, status="active")
    db.get = AsyncMock(return_value=user)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.update_user(db, user.id, {"status": "disabled"})
    assert exc_info.value.error_code == "E10203"


@pytest.mark.asyncio
async def test_update_user_last_active_protection():
    db = AsyncMock(spec=AsyncSession)
    user = _make_user(status="active")
    db.get = AsyncMock(return_value=user)

    count_result = MagicMock()
    count_result.scalar.return_value = 0
    db.execute = AsyncMock(return_value=count_result)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.update_user(db, user.id, {"status": "disabled"})
    assert exc_info.value.error_code == "E10204"


@pytest.mark.asyncio
async def test_delete_user_must_be_disabled():
    db = AsyncMock(spec=AsyncSession)
    user = _make_user(status="active", is_builtin=False)
    db.get = AsyncMock(return_value=user)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.delete_user(db, user.id)
    assert exc_info.value.error_code == "E10204"


@pytest.mark.asyncio
async def test_delete_user_builtin_protected():
    db = AsyncMock(spec=AsyncSession)
    user = _make_user(is_builtin=True)
    db.get = AsyncMock(return_value=user)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.delete_user(db, user.id)
    assert exc_info.value.error_code == "E10203"


@pytest.mark.asyncio
async def test_reset_password_not_found():
    db = AsyncMock(spec=AsyncSession)
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.reset_password(db, uuid4(), "NewPass1234")
    assert exc_info.value.error_code == "E10202"


@pytest.mark.asyncio
async def test_assign_role_user_not_found():
    db = AsyncMock(spec=AsyncSession)
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await user_service.assign_role(db, uuid4(), uuid4())
    assert exc_info.value.error_code == "E10202"
