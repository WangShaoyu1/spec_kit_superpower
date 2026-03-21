"""Unit tests for app.services.testing.batch_service."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.services.testing.batch_service import (
    delete_batch,
    get_batch,
    refresh_case_count,
    transition_status,
)


def _mock_db_execute_returns(value):
    """Build an AsyncMock(spec=AsyncSession) whose execute() chain yields *value*."""
    db = AsyncMock(spec=AsyncSession)
    row = MagicMock()
    row.unique.return_value.scalars.return_value.first.return_value = value
    row.scalar.return_value = value
    db.execute.return_value = row
    return db


class TestGetBatch:
    async def test_get_batch_not_found(self):
        db = _mock_db_execute_returns(None)

        with pytest.raises(BusinessException) as exc_info:
            await get_batch(db, uuid.uuid4())

        assert exc_info.value.error_code == "E50101"


class TestDeleteBatch:
    async def test_delete_batch_not_found(self):
        db = _mock_db_execute_returns(None)

        with pytest.raises(BusinessException) as exc_info:
            await delete_batch(db, uuid.uuid4())

        assert exc_info.value.error_code == "E50101"


class TestTransitionStatus:
    async def test_transition_draft_to_ready(self):
        db = AsyncMock(spec=AsyncSession)
        batch = MagicMock()
        batch.status = "draft"

        result = await transition_status(db, batch, "ready")

        assert result.status == "ready"
        db.flush.assert_awaited_once()

    async def test_transition_draft_to_running(self):
        db = AsyncMock(spec=AsyncSession)
        batch = MagicMock()
        batch.status = "draft"

        with pytest.raises(BusinessException) as exc_info:
            await transition_status(db, batch, "running")

        assert exc_info.value.error_code == "E50102"

    async def test_transition_ready_to_running(self):
        db = AsyncMock(spec=AsyncSession)
        batch = MagicMock()
        batch.status = "ready"

        result = await transition_status(db, batch, "running")

        assert result.status == "running"

    async def test_transition_running_to_completed(self):
        db = AsyncMock(spec=AsyncSession)
        batch = MagicMock()
        batch.status = "running"

        result = await transition_status(db, batch, "completed")

        assert result.status == "completed"

    async def test_transition_completed_to_running(self):
        db = AsyncMock(spec=AsyncSession)
        batch = MagicMock()
        batch.status = "completed"

        with pytest.raises(BusinessException) as exc_info:
            await transition_status(db, batch, "running")

        assert exc_info.value.error_code == "E50102"


class TestRefreshCaseCount:
    async def test_refresh_case_count_auto_ready(self):
        db = AsyncMock(spec=AsyncSession)
        scalar_result = MagicMock()
        scalar_result.scalar.return_value = 5
        db.execute.return_value = scalar_result

        batch = MagicMock()
        batch.status = "draft"
        batch.id = uuid.uuid4()

        result = await refresh_case_count(db, batch)

        assert result.total_cases == 5
        assert result.status == "ready"

    async def test_refresh_case_count_auto_draft(self):
        db = AsyncMock(spec=AsyncSession)
        scalar_result = MagicMock()
        scalar_result.scalar.return_value = 0
        db.execute.return_value = scalar_result

        batch = MagicMock()
        batch.status = "ready"
        batch.id = uuid.uuid4()

        result = await refresh_case_count(db, batch)

        assert result.total_cases == 0
        assert result.status == "draft"
