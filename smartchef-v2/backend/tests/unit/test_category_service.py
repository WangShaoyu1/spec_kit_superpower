"""Unit tests for app.services.knowledge.category_service."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.schemas.knowledge import CreateCategoryRequest, UpdateCategoryRequest
from app.services.knowledge.category_service import (
    create_category,
    delete_category,
    update_category,
)


def _fake_category(cat_id=None, name="Test", parent_id=None):
    """Return a MagicMock that behaves like a KnowledgeCategory row."""
    cat = MagicMock()
    cat.id = cat_id or uuid.uuid4()
    cat.name = name
    cat.description = None
    cat.parent_id = parent_id
    cat.sort_order = 0
    cat.created_by = None
    cat.created_at = None
    cat.updated_at = None
    return cat


class TestCreateCategory:
    async def test_create_category_success(self):
        db = AsyncMock(spec=AsyncSession)
        data = CreateCategoryRequest(name="Recipes")

        result = await create_category(db, data, user_id="user-1")

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        assert result["name"] == "Recipes"

    async def test_create_category_parent_not_found(self):
        db = AsyncMock(spec=AsyncSession)
        db.get.return_value = None
        parent_id = uuid.uuid4()
        data = CreateCategoryRequest(name="Subcategory", parent_id=parent_id)

        with pytest.raises(BusinessException) as exc_info:
            await create_category(db, data, user_id="user-1")

        assert exc_info.value.error_code == "E60101"


class TestUpdateCategory:
    async def test_update_category_not_found(self):
        db = AsyncMock(spec=AsyncSession)
        db.get.return_value = None
        data = UpdateCategoryRequest(name="Updated")

        with pytest.raises(BusinessException) as exc_info:
            await update_category(db, uuid.uuid4(), data)

        assert exc_info.value.error_code == "E60101"

    async def test_update_category_self_reference(self):
        cat_id = uuid.uuid4()
        cat = _fake_category(cat_id=cat_id)

        db = AsyncMock(spec=AsyncSession)
        db.get.return_value = cat
        data = UpdateCategoryRequest(parent_id=cat_id)

        with pytest.raises(BusinessException) as exc_info:
            await update_category(db, cat_id, data)

        assert exc_info.value.error_code == "E60101"


class TestDeleteCategory:
    async def test_delete_category_has_children(self):
        cat_id = uuid.uuid4()
        cat = _fake_category(cat_id=cat_id)

        db = AsyncMock(spec=AsyncSession)
        db.get.return_value = cat

        child_scalar = MagicMock()
        child_scalar.scalar.return_value = 2
        db.execute.return_value = child_scalar

        with pytest.raises(BusinessException) as exc_info:
            await delete_category(db, cat_id)

        assert exc_info.value.error_code == "E60102"

    async def test_delete_category_has_documents(self):
        cat_id = uuid.uuid4()
        cat = _fake_category(cat_id=cat_id)

        db = AsyncMock(spec=AsyncSession)
        db.get.return_value = cat

        child_scalar = MagicMock()
        child_scalar.scalar.return_value = 0
        doc_scalar = MagicMock()
        doc_scalar.scalar.return_value = 3
        db.execute.side_effect = [child_scalar, doc_scalar]

        with pytest.raises(BusinessException) as exc_info:
            await delete_category(db, cat_id)

        assert exc_info.value.error_code == "E60103"
