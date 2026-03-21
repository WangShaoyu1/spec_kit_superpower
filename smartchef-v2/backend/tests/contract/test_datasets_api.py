"""Contract tests for app.api.v1.datasets routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

LIB_ID = str(uuid.uuid4())
DS_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.datasets.dataset_service"


@pytest.mark.asyncio
async def test_list_training_datasets_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_training_datasets = AsyncMock(return_value=(
            [{"id": DS_ID, "name": "train1", "library_id": LIB_ID}],
            1,
        ))
        resp = await client.get(
            f"/api/v1/intent-libraries/{LIB_ID}/datasets",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["total"] == 1
    assert len(body["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_create_training_dataset_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name": "train1", "source_type": "manual"}
    with patch(PATCH_SVC) as svc:
        svc.create_training_dataset = AsyncMock(return_value={
            "id": DS_ID, "library_id": LIB_ID, **payload,
        })
        resp = await client.post(
            f"/api/v1/intent-libraries/{LIB_ID}/datasets",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == DS_ID


@pytest.mark.asyncio
async def test_get_training_dataset_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_training_dataset = AsyncMock(return_value={
            "id": DS_ID, "name": "train1", "library_id": LIB_ID,
        })
        resp = await client.get(f"/api/v1/datasets/{DS_ID}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == DS_ID


@pytest.mark.asyncio
async def test_update_training_dataset_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name": "renamed"}
    with patch(PATCH_SVC) as svc:
        svc.update_training_dataset = AsyncMock(return_value={
            "id": DS_ID, "name": "renamed", "library_id": LIB_ID,
        })
        resp = await client.put(
            f"/api/v1/datasets/{DS_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "renamed"


@pytest.mark.asyncio
async def test_delete_training_dataset_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_training_dataset = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/datasets/{DS_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_list_evaluation_datasets_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_evaluation_datasets = AsyncMock(return_value=(
            [{"id": DS_ID, "name": "eval1", "library_id": LIB_ID}],
            1,
        ))
        resp = await client.get(
            f"/api/v1/intent-libraries/{LIB_ID}/eval-datasets",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["total"] == 1


@pytest.mark.asyncio
async def test_create_evaluation_dataset_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name": "eval1", "source_type": "manual"}
    with patch(PATCH_SVC) as svc:
        svc.create_evaluation_dataset = AsyncMock(return_value={
            "id": DS_ID, "library_id": LIB_ID, **payload,
        })
        resp = await client.post(
            f"/api/v1/intent-libraries/{LIB_ID}/eval-datasets",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == DS_ID


@pytest.mark.asyncio
async def test_update_evaluation_dataset_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"samples": [{"text": "hi"}], "sample_count": 1, "name": "e2"}
    with patch(PATCH_SVC) as svc:
        svc.update_evaluation_dataset = AsyncMock(return_value={
            "id": DS_ID, "name": "e2", "sample_count": 1,
        })
        resp = await client.put(
            f"/api/v1/eval-datasets/{DS_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "e2"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get(f"/api/v1/intent-libraries/{LIB_ID}/datasets")
    assert resp.status_code == 401
