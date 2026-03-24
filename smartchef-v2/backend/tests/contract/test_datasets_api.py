"""Contract tests for app.api.v1.datasets routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

LIB_ID = str(uuid.uuid4())
DS_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.datasets.dataset_service"
PATCH_GEN_SVC = "app.api.v1.datasets.data_generation_service"
PATCH_TRAIN_JOB = "app.api.v1.datasets.training_gen_job"


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
async def test_get_evaluation_dataset_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_evaluation_dataset = AsyncMock(return_value={
            "id": DS_ID, "name": "eval1", "library_id": LIB_ID,
        })
        resp = await client.get(f"/api/v1/eval-datasets/{DS_ID}", headers=headers)
    assert resp.status_code == 200
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
async def test_generate_evaluation_dataset_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"model_name": "gpt-4o", "samples_per_intent": 20}
    with patch(PATCH_GEN_SVC) as svc:
        svc.generate_evaluation_data = AsyncMock(return_value={
            "generated_count": 12,
            "dataset_id": DS_ID,
        })
        resp = await client.post(
            f"/api/v1/datasets/{DS_ID}/generate-evaluation",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["generated_count"] == 12


@pytest.mark.asyncio
async def test_start_training_generation_job_202(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"model_name": "gpt-4o", "samples_per_intent": 20}
    with patch(f"{PATCH_TRAIN_JOB}.save_job_state", new=AsyncMock()), patch(
        f"{PATCH_TRAIN_JOB}.run_training_generation_job", new=AsyncMock(),
    ):
        resp = await client.post(
            f"/api/v1/datasets/{DS_ID}/generate-training/jobs",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 202
    body = resp.json()
    assert body["code"] == "000000"
    assert "job_id" in body["data"]
    assert body["data"].get("poll_interval_sec") == 6


@pytest.mark.asyncio
async def test_get_training_generation_job_200(client):
    headers = make_auth_header()
    fake = {
        "job_id": "job-1",
        "dataset_id": DS_ID,
        "status": "running",
        "intent_index": 1,
        "intent_total": 3,
        "generated_count": 10,
    }
    with patch(f"{PATCH_TRAIN_JOB}.load_job_state", new=AsyncMock(return_value=fake)):
        resp = await client.get(
            f"/api/v1/datasets/{DS_ID}/generate-training/jobs/job-1",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["status"] == "running"


@pytest.mark.asyncio
async def test_generate_training_dataset_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"model_name": "gpt-4o", "samples_per_intent": 20}
    with patch(PATCH_GEN_SVC) as svc:
        svc.generate_training_data = AsyncMock(return_value={
            "generated_count": 18,
            "dataset_id": DS_ID,
        })
        resp = await client.post(
            f"/api/v1/datasets/{DS_ID}/generate-training",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["generated_count"] == 18


@pytest.mark.asyncio
async def test_delete_evaluation_dataset_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_evaluation_dataset = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/eval-datasets/{DS_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get(f"/api/v1/intent-libraries/{LIB_ID}/datasets")
    assert resp.status_code == 401
