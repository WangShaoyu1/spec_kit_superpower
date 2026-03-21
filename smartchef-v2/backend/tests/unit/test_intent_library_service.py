"""Unit tests for IntentLibrary CRUD service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.schemas.intent_library import CreateLibraryRequest, UpdateLibraryRequest
from app.services import intent_library_service


@pytest.fixture
def db():
    mock = AsyncMock(spec=AsyncSession)
    mock.flush = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def sample_create_data():
    return CreateLibraryRequest(
        library_key="test_lib",
        name="Test Library",
        language="zh",
    )


@pytest.fixture
def mock_library():
    lib = MagicMock()
    lib.id = uuid4()
    lib.library_key = "test_lib"
    lib.name = "Test Library"
    lib.language = "zh"
    lib.description = "A test library"
    lib.default_confidence_threshold = 0.7
    lib.default_intent_f1_threshold = 0.95
    lib.default_slot_f1_threshold = 0.90
    lib.created_by = uuid4()
    lib.created_at = None
    lib.updated_at = None
    return lib


async def test_create_library_success(db, sample_create_data):
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    result = await intent_library_service.create_library(db, sample_create_data, str(uuid4()))

    assert isinstance(result, dict)
    assert result["library_key"] == "test_lib"
    assert result["name"] == "Test Library"
    assert result["language"] == "zh"
    db.add.assert_called_once()
    db.flush.assert_awaited_once()


async def test_create_library_duplicate_key(db, sample_create_data):
    mock_result = MagicMock()
    mock_result.scalar.return_value = MagicMock()
    db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(BusinessException) as exc:
        await intent_library_service.create_library(db, sample_create_data, str(uuid4()))

    assert exc.value.error_code == "E50101"


async def test_create_library_zh_cn_normalized_to_zh(db):
    """入参 zh-CN 存储前归一化为 zh"""
    data = CreateLibraryRequest(library_key="test_zh_cn", name="中文库", language="zh-CN")
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    result = await intent_library_service.create_library(db, data, str(uuid4()))

    assert result["language"] == "zh"


async def test_create_library_zh_language(db):
    """D020: 支持 zh/en（DD §4.1 语言仅支持 zh 或 en）"""
    data = CreateLibraryRequest(library_key="test_zh", name="中文库", language="zh")
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    result = await intent_library_service.create_library(db, data, str(uuid4()))

    assert result["language"] == "zh"


async def test_create_library_zh_cn_normalized_to_zh(db):
    """入参 zh-CN 归一化存储为 zh"""
    data = CreateLibraryRequest(library_key="test_zh_cn", name="中文库", language="zh-CN")
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    result = await intent_library_service.create_library(db, data, str(uuid4()))

    assert result["language"] == "zh"


async def test_create_library_invalid_language(db):
    data = CreateLibraryRequest.model_construct(
        library_key="test_lib",
        name="Test",
        language="invalid_lang",
        description=None,
        default_confidence_threshold=0.7,
        default_intent_f1_threshold=0.95,
        default_slot_f1_threshold=0.90,
    )
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(BusinessException) as exc:
        await intent_library_service.create_library(db, data, str(uuid4()))

    assert exc.value.error_code == "E50103"


async def test_get_library_not_found(db):
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc:
        await intent_library_service.get_library(db, uuid4())

    assert exc.value.error_code == "E50102"


async def test_update_library_not_found(db):
    db.get = AsyncMock(return_value=None)
    data = UpdateLibraryRequest(name="Updated Name")

    with pytest.raises(BusinessException) as exc:
        await intent_library_service.update_library(db, uuid4(), data)

    assert exc.value.error_code == "E50102"


async def test_delete_library_not_found(db):
    db.get = AsyncMock(return_value=None)

    with pytest.raises(BusinessException) as exc:
        await intent_library_service.delete_library(db, uuid4())

    assert exc.value.error_code == "E50102"


async def test_delete_library_has_active_models(db, mock_library):
    db.get = AsyncMock(return_value=mock_library)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 2
    db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(BusinessException) as exc:
        await intent_library_service.delete_library(db, mock_library.id)

    assert exc.value.error_code == "E50120"


async def test_delete_library_success(db, mock_library):
    db.get = AsyncMock(return_value=mock_library)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    db.execute = AsyncMock(return_value=mock_result)

    await intent_library_service.delete_library(db, mock_library.id)

    db.delete.assert_awaited_once_with(mock_library)
    db.flush.assert_awaited_once()
