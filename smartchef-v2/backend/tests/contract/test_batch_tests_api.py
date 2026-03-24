"""Contract tests for /api/v1/batch-tests endpoints."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

_READ = make_auth_header(["batch_test_read"])
_WRITE = make_auth_header(["batch_test_write"])
_EXEC = make_auth_header(["batch_test_execute"])


def _fake_batch(**kw):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid.uuid4(),
        name="Batch-1",
        description=None,
        profile_id=None,
        model_id=None,
        status="pending",
        total_cases=0,
        completed_cases=0,
        accuracy=None,
        precision_score=None,
        recall_score=None,
        accuracy_threshold=None,
        latency_threshold_ms=None,
        p99_latency_ms=None,
        created_by=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(kw)
    obj = SimpleNamespace(**defaults)
    obj.profile = None
    return obj


@pytest.mark.asyncio
async def test_list_batches_200(client):
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.list_batches = AsyncMock(return_value=([], 0))
        resp = await client.get("/api/v1/batch-tests", headers=_READ)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


@pytest.mark.asyncio
async def test_create_batch_200(client):
    batch = _fake_batch()
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.create_batch = AsyncMock(return_value=batch)
        resp = await client.post(
            "/api/v1/batch-tests",
            json={"name": "Test Batch"},
            headers=_WRITE,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "Batch-1"
    assert body["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_create_batch_with_model_id_200(client):
    model_id = uuid.uuid4()
    batch = _fake_batch(model_id=model_id)
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.create_batch = AsyncMock(return_value=batch)
        resp = await client.post(
            "/api/v1/batch-tests",
            json={"name": "Model Batch", "model_id": str(model_id)},
            headers=_WRITE,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["model_id"] == str(model_id)


@pytest.mark.asyncio
async def test_get_batch_200(client):
    batch = _fake_batch()
    bid = str(batch.id)
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.get_batch = AsyncMock(return_value=batch)
        resp = await client.get(f"/api/v1/batch-tests/{bid}", headers=_READ)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == bid


@pytest.mark.asyncio
async def test_get_batch_with_model_id_200(client):
    model_id = uuid.uuid4()
    batch = _fake_batch(model_id=model_id)
    bid = str(batch.id)
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.get_batch = AsyncMock(return_value=batch)
        resp = await client.get(f"/api/v1/batch-tests/{bid}", headers=_READ)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["model_id"] == str(model_id)


@pytest.mark.asyncio
async def test_get_batch_404(client):
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.get_batch = AsyncMock(
            side_effect=BusinessException("E50101", "批量测试不存在", http_status=404),
        )
        resp = await client.get(
            f"/api/v1/batch-tests/{uuid.uuid4()}", headers=_READ,
        )
    assert resp.status_code == 404
    assert resp.json()["code"] == "E50101"


@pytest.mark.asyncio
async def test_delete_batch_200(client):
    with patch("app.api.v1.batch_tests.batch_service") as svc:
        svc.delete_batch = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/batch-tests/{uuid.uuid4()}", headers=_WRITE,
        )
    assert resp.status_code == 200
    assert resp.json()["code"] == "000000"


@pytest.mark.asyncio
async def test_execute_batch_200(client):
    batch = _fake_batch(status="completed")
    with patch("app.api.v1.batch_tests.batch_executor") as exe:
        exe.execute_batch = AsyncMock(return_value=batch)
        resp = await client.post(
            f"/api/v1/batch-tests/{batch.id}/execute", headers=_EXEC,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_list_cases_200(client):
    case_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    with patch("app.api.v1.batch_tests.case_service") as case_svc:
        case_svc.list_cases = AsyncMock(return_value=(
            [{
                "id": str(case_id),
                "batch_id": str(batch_id),
                "input_text": "打开烤箱",
                "expected_intent": "device.on",
                "expected_slots": {},
                "expected_domain": "command",
                "sort_order": 0,
                "created_at": "2026-03-23T00:00:00Z",
            }],
            1,
        ))
        resp = await client.get(f"/api/v1/batch-tests/{batch_id}/cases", headers=_READ)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["items"][0]["id"] == str(case_id)
    assert body["data"]["items"][0]["batch_id"] == str(batch_id)


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get("/api/v1/batch-tests")
    assert resp.status_code == 401
