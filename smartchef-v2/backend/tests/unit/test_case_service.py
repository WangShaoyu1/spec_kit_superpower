"""Unit tests for app.services.testing.case_service."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.testing.case_service import list_cases


@pytest.mark.asyncio
async def test_list_cases_serializes_uuid_fields_to_json_safe_strings():
    batch_id = uuid.uuid4()
    case = SimpleNamespace(
        id=uuid.uuid4(),
        batch_id=batch_id,
        input_text="打开烤箱",
        expected_intent="device.on",
        expected_slots={},
        expected_domain="command",
        sort_order=0,
        created_at=datetime.now(timezone.utc),
    )

    count_result = MagicMock()
    count_result.scalar.return_value = 1
    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = [case]

    db = AsyncMock(spec=AsyncSession)
    db.execute.side_effect = [count_result, rows_result]

    items, total = await list_cases(db, batch_id)

    assert total == 1
    assert items[0]["id"] == str(case.id)
    assert items[0]["batch_id"] == str(batch_id)
