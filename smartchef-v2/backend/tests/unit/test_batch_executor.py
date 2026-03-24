"""Unit tests for app.services.testing.batch_executor."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.services.testing import batch_executor


def _batch(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "model_id": uuid.uuid4(),
        "profile_id": None,
        "status": "ready",
        "total_cases": 1,
        "completed_cases": 0,
        "accuracy": None,
        "precision_score": None,
        "recall_score": None,
        "p99_latency_ms": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _case(**kwargs):
    defaults = {
        "id": uuid.uuid4(),
        "input_text": "打开烤箱",
        "expected_domain": "command",
        "expected_intent": "device.on",
        "expected_slots": {},
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.mark.asyncio
async def test_execute_batch_uses_model_inference_when_model_id_present():
    db = AsyncMock(spec=AsyncSession)
    batch = _batch()
    case = _case()
    cases_result = MagicMock()
    cases_result.scalars.return_value.all.return_value = [case]
    db.execute.side_effect = [None, None, cases_result]

    with patch("app.services.testing.batch_executor.batch_service") as svc, patch(
        "app.services.testing.batch_executor._infer_with_model"
    ) as infer:
        svc.get_batch = AsyncMock(return_value=batch)
        svc.transition_status = AsyncMock(side_effect=lambda _db, obj, status: setattr(obj, "status", status) or obj)
        infer.return_value = {
            "domain": "command",
            "intent": "device.on",
            "slots": {"device": "烤箱"},
            "confidence": 0.97,
        }

        result = await batch_executor.execute_batch(db, batch.id)

    assert result.status == "completed"
    infer.assert_awaited_once_with(db, batch.model_id, case.input_text)
    assert batch.completed_cases == 1


@pytest.mark.asyncio
async def test_execute_batch_rejects_batches_without_target():
    db = AsyncMock(spec=AsyncSession)
    batch = _batch(model_id=None, profile_id=None)

    with patch("app.services.testing.batch_executor.batch_service") as svc:
        svc.get_batch = AsyncMock(return_value=batch)

        with pytest.raises(BusinessException) as exc_info:
            await batch_executor.execute_batch(db, batch.id)

    assert exc_info.value.error_code == "E50104"
