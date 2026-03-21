"""Unit tests for app.services.role_service — mock-based, no real DB."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.services import role_service


def _make_role(*, role_id=None, name="custom-role", is_builtin=False, description=None):
    role = MagicMock()
    role.id = role_id or uuid4()
    role.name = name
    role.description = description
    role.is_builtin = is_builtin
    role.created_at = datetime.now(timezone.utc)
    return role


@pytest.mark.asyncio
async def test_create_role_success():
    db = AsyncMock(spec=AsyncSession)

    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = None
    perm_result = MagicMock()
    perm_result.scalars.return_value.all.return_value = ["intent_manage"]
    db.execute = AsyncMock(side_effect=[dup_result, perm_result])

    async def fake_refresh(obj, **kwargs):
        obj.id = uuid4()
        obj.created_at = datetime.now(timezone.utc)

    db.refresh = AsyncMock(side_effect=fake_refresh)

    data = {"name": "editor", "description": "Can edit", "permission_keys": []}
    result = await role_service.create_role(db, data)

    assert result["name"] == "editor"
    assert not result["is_builtin"]
    db.add.assert_called_once()
    db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_create_role_duplicate_name():
    db = AsyncMock(spec=AsyncSession)

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = _make_role(name="admin")
    db.execute = AsyncMock(return_value=exec_result)

    with pytest.raises(BusinessException) as exc_info:
        await role_service.create_role(db, {"name": "admin"})
    assert exc_info.value.error_code == "E10301"


@pytest.mark.asyncio
async def test_get_role_not_found():
    db = AsyncMock(spec=AsyncSession)
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await role_service.get_role(db, uuid4())
    assert exc_info.value.error_code == "E10302"


@pytest.mark.asyncio
async def test_update_role_builtin_name_protected():
    db = AsyncMock(spec=AsyncSession)
    role = _make_role(is_builtin=True, name="admin")
    db.get = AsyncMock(return_value=role)

    with pytest.raises(BusinessException) as exc_info:
        await role_service.update_role(db, role.id, {"name": "renamed"})
    assert exc_info.value.error_code == "E10303"


@pytest.mark.asyncio
async def test_update_role_duplicate_name():
    db = AsyncMock(spec=AsyncSession)
    role = _make_role(is_builtin=False, name="editor")
    db.get = AsyncMock(return_value=role)

    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = _make_role(name="taken")
    db.execute = AsyncMock(return_value=dup_result)

    with pytest.raises(BusinessException) as exc_info:
        await role_service.update_role(db, role.id, {"name": "taken"})
    assert exc_info.value.error_code == "E10301"


@pytest.mark.asyncio
async def test_delete_role_builtin_protected():
    db = AsyncMock(spec=AsyncSession)
    role = _make_role(is_builtin=True, name="admin")
    db.get = AsyncMock(return_value=role)

    with pytest.raises(BusinessException) as exc_info:
        await role_service.delete_role(db, role.id)
    assert exc_info.value.error_code == "E10303"


@pytest.mark.asyncio
async def test_delete_role_has_users():
    db = AsyncMock(spec=AsyncSession)
    role = _make_role(is_builtin=False)
    db.get = AsyncMock(return_value=role)

    count_result = MagicMock()
    count_result.scalar.return_value = 3
    db.execute = AsyncMock(return_value=count_result)

    with pytest.raises(BusinessException) as exc_info:
        await role_service.delete_role(db, role.id)
    assert exc_info.value.error_code == "E10304"


@pytest.mark.asyncio
async def test_delete_role_success():
    db = AsyncMock(spec=AsyncSession)
    role = _make_role(is_builtin=False)
    db.get = AsyncMock(return_value=role)

    count_result = MagicMock()
    count_result.scalar.return_value = 0
    db.execute = AsyncMock(return_value=count_result)

    await role_service.delete_role(db, role.id)

    db.delete.assert_awaited_once_with(role)
    db.flush.assert_awaited()
