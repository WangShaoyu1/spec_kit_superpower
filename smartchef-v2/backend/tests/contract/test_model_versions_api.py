"""Contract tests for app.api.v1.model_versions routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

LIB_ID = str(uuid.uuid4())
MODEL_ID = str(uuid.uuid4())
RUN_ID = str(uuid.uuid4())
DATASET_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.model_versions.model_version_service"
# 延迟 import 后需 patch 路由模块内的后台入口，而非 trainer 模块顶层符号
PATCH_BG_TRAIN = "app.api.v1.model_versions._run_training_background"
PATCH_BG_EVAL = "app.api.v1.model_versions._run_evaluation_background"


@pytest.mark.asyncio
async def test_list_models_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_model_versions = AsyncMock(return_value=[
            {"id": MODEL_ID, "version_name": "v1", "status": "draft"},
        ])
        resp = await client.get(
            f"/api/v1/intent-libraries/{LIB_ID}/models", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == MODEL_ID


@pytest.mark.asyncio
async def test_create_model_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"version_name": "v1", "train_config": {}}
    with patch(PATCH_SVC) as svc:
        svc.create_model_version = AsyncMock(return_value={
            "id": MODEL_ID, "library_id": LIB_ID, "version_name": "v1",
            "status": "draft",
        })
        resp = await client.post(
            f"/api/v1/intent-libraries/{LIB_ID}/models",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == MODEL_ID


@pytest.mark.asyncio
async def test_start_training_200(client):
    headers = make_auth_header(["intent_library_write"])
    with patch(PATCH_SVC) as svc, patch(PATCH_BG_TRAIN, new=AsyncMock()):
        svc.start_training = AsyncMock(return_value={
            "id": MODEL_ID, "status": "training", "progress": 0,
        })
        resp = await client.post(
            f"/api/v1/models/{MODEL_ID}/train",
            json={},
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["status"] == "training"


@pytest.mark.asyncio
async def test_start_evaluation_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"dataset_id": DATASET_ID}
    with patch(PATCH_SVC) as svc, patch(PATCH_BG_EVAL, new=AsyncMock()):
        svc.start_evaluation = AsyncMock(return_value={
            "id": RUN_ID,
            "model_version_id": MODEL_ID,
            "dataset_id": DATASET_ID,
            "status": "pending",
        })
        resp = await client.post(
            f"/api/v1/models/{MODEL_ID}/evaluate",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == RUN_ID


@pytest.mark.asyncio
async def test_set_testable_200(client):
    headers = make_auth_header(["intent_library_write"])
    with patch(PATCH_SVC) as svc:
        svc.set_testable = AsyncMock(return_value={
            "id": MODEL_ID, "status": "testable", "is_testable": True,
        })
        resp = await client.post(
            f"/api/v1/models/{MODEL_ID}/set-testable",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["is_testable"] is True


@pytest.mark.asyncio
async def test_publish_model_200(client):
    headers = make_auth_header(["model_publish"])
    with patch(PATCH_SVC) as svc:
        svc.publish_model = AsyncMock(return_value={
            "id": MODEL_ID, "status": "published", "is_published": True,
        })
        resp = await client.post(
            f"/api/v1/models/{MODEL_ID}/publish",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["is_published"] is True


@pytest.mark.asyncio
async def test_archive_model_200(client):
    headers = make_auth_header(["intent_library_write"])
    with patch(PATCH_SVC) as svc:
        svc.archive_model = AsyncMock(return_value={
            "id": MODEL_ID, "status": "archived",
        })
        resp = await client.post(
            f"/api/v1/models/{MODEL_ID}/archive",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["status"] == "archived"


@pytest.mark.asyncio
async def test_get_model_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_model_version = AsyncMock(return_value={
            "id": MODEL_ID,
            "version_name": "v1",
            "status": "trained",
            "package_uri": "s3://pkg",
            "artifact_uri": "/artifacts/m",
            "artifact_sha256": "abc123",
        })
        resp = await client.get(f"/api/v1/models/{MODEL_ID}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == MODEL_ID


@pytest.mark.asyncio
async def test_download_model_200(client, tmp_path):
    """D039: 下载端点返回 zip 文件流，非 JSON 包裹。"""
    headers = make_auth_header()
    zip_path = tmp_path / "package.zip"
    zip_path.write_bytes(b"PK\x03\x04" + b"fake-zip-bytes")
    with patch(PATCH_SVC) as svc, patch(
        "app.api.v1.model_versions.resolve_artifact_path",
        return_value=str(zip_path),
    ):
        svc.get_model_version = AsyncMock(return_value={
            "id": MODEL_ID,
            "package_uri": "data/models/foo/package.zip",
        })
        resp = await client.get(
            f"/api/v1/models/{MODEL_ID}/download", headers=headers,
        )
    assert resp.status_code == 200
    assert b"PK" in resp.content
    assert resp.headers.get("content-type", "").startswith("application/")


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get(f"/api/v1/intent-libraries/{LIB_ID}/models")
    assert resp.status_code == 401
