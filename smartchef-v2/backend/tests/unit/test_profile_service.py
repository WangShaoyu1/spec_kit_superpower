"""Unit tests for Dialog Profile CRUD service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.schemas.profile import CreateProfileRequest, UpdateProfileRequest
from app.services import profile_service


@pytest.fixture
def db():
    mock = AsyncMock(spec=AsyncSession)
    mock.flush = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def sample_create_data():
    return CreateProfileRequest(
        name="Test Profile",
        description="A test dialog profile",
        command_threshold=0.7,
        route_strategy="intent_first",
        llm_provider="openai",
        llm_model="gpt-4",
        session_timeout_min=10,
    )


@pytest.fixture
def mock_profile():
    profile = MagicMock()
    profile.id = uuid4()
    profile.name = "Test Profile"
    profile.description = "A test dialog profile"
    profile.status = "draft"
    profile.command_threshold = 0.7
    profile.route_strategy = "intent_first"
    profile.llm_provider = "openai"
    profile.llm_model = "gpt-4"
    profile.session_timeout_min = 10
    profile.created_by = uuid4()
    profile.created_at = None
    profile.updated_at = None
    profile.library_bindings = []
    return profile


async def test_create_profile_success(db, sample_create_data):
    result = await profile_service.create_profile(db, sample_create_data, str(uuid4()))

    assert isinstance(result, dict)
    assert result["name"] == "Test Profile"
    assert result["route_strategy"] == "intent_first"
    db.add.assert_called_once()
    db.flush.assert_awaited_once()


async def test_get_profile_not_found(db):
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc:
        await profile_service.get_profile(db, uuid4())

    assert exc.value.error_code == "E40101"


async def test_update_profile_not_found(db):
    db.get = AsyncMock(return_value=None)
    data = UpdateProfileRequest(name="Updated Name")

    with pytest.raises(BusinessException) as exc:
        await profile_service.update_profile(db, uuid4(), data)

    assert exc.value.error_code == "E40101"


async def test_delete_profile_not_found(db):
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc:
        await profile_service.delete_profile(db, uuid4())

    assert exc.value.error_code == "E40101"


async def test_delete_profile_has_active_version(db, mock_profile):
    db.get = AsyncMock(return_value=mock_profile)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(BusinessException) as exc:
        await profile_service.delete_profile(db, mock_profile.id)

    assert exc.value.error_code == "E40102"


async def test_delete_profile_success(db, mock_profile):
    db.get = AsyncMock(return_value=mock_profile)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    db.execute = AsyncMock(return_value=mock_result)

    await profile_service.delete_profile(db, mock_profile.id)

    db.delete.assert_awaited_once_with(mock_profile)
    db.flush.assert_awaited_once()
