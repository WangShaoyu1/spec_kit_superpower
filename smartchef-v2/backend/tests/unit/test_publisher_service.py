"""Unit tests for app.services.publisher_service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.services.publisher_service import (
    archive_version,
    get_version,
    publish,
    _next_version_number,
)


def _mock_db() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_publish_profile_not_found():
    db = _mock_db()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await publish(db, uuid4(), str(uuid4()))

    assert exc_info.value.error_code == "E40101"


@pytest.mark.asyncio
async def test_publish_no_bindings():
    db = _mock_db()

    mock_profile = MagicMock()
    mock_profile.id = uuid4()
    mock_profile.library_bindings = []
    mock_profile.personas = []
    db.get = AsyncMock(return_value=mock_profile)

    with pytest.raises(BusinessException) as exc_info:
        await publish(db, mock_profile.id, str(uuid4()))

    assert exc_info.value.error_code == "E40301"


@pytest.mark.asyncio
async def test_publish_missing_published_model():
    db = _mock_db()

    binding = MagicMock()
    binding.library_id = uuid4()
    binding.priority = 0
    binding.confidence_threshold = 0.7

    mock_profile = MagicMock()
    mock_profile.id = uuid4()
    mock_profile.library_bindings = [binding]
    mock_profile.personas = []
    db.get = AsyncMock(return_value=mock_profile)

    scalar_result = MagicMock()
    scalar_result.scalar.return_value = 0
    db.execute = AsyncMock(return_value=scalar_result)

    with pytest.raises(BusinessException) as exc_info:
        await publish(db, mock_profile.id, str(uuid4()))

    assert exc_info.value.error_code == "E40301"


@pytest.mark.asyncio
async def test_get_version_not_found():
    db = _mock_db()
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc_info:
        await get_version(db, uuid4())

    assert exc_info.value.error_code == "E40302"


@pytest.mark.asyncio
async def test_archive_already_archived():
    db = _mock_db()

    version = MagicMock()
    version.id = uuid4()
    version.status = "archived"
    db.get = AsyncMock(return_value=version)

    with pytest.raises(BusinessException) as exc_info:
        await archive_version(db, version.id)

    assert exc_info.value.error_code == "E40303"


@pytest.mark.asyncio
async def test_version_number_increment():
    db = _mock_db()

    scalar_result = MagicMock()
    scalar_result.scalar.return_value = "v1.0"
    db.execute = AsyncMock(return_value=scalar_result)

    result = await _next_version_number(db, uuid4())
    assert result == "v2.0"
