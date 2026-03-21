"""Integration tests for Intent Library CRUD — runs against real DB + Redis."""

import uuid

import pytest

from tests.integration.conftest import login_as_admin

PREFIX = "/api/v1/intent-libraries"


def _unique_key() -> str:
    return f"lib_{uuid.uuid4().hex[:8]}"


async def _auth_headers(client) -> dict[str, str]:
    data = await login_as_admin(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_library(client, headers, *, key: str | None = None, name: str = "Test Library"):
    payload = {
        "library_key": key or _unique_key(),
        "name": name,
        "language": "zh",
    }
    resp = await client.post(PREFIX, json=payload, headers=headers)
    return resp


@pytest.mark.asyncio
async def test_create_and_list_library(client):
    headers = await _auth_headers(client)
    key = _unique_key()

    create_resp = await _create_library(client, headers, key=key, name="Cooking Lib")
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["code"] == "000000"
    assert body["data"]["library_key"] == key

    list_resp = await client.get(PREFIX, headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert any(item["library_key"] == key for item in items)


@pytest.mark.asyncio
async def test_get_library_detail(client):
    headers = await _auth_headers(client)

    create_resp = await _create_library(client, headers, name="Detail Lib")
    assert create_resp.status_code == 201
    lib_id = create_resp.json()["data"]["id"]

    get_resp = await client.get(f"{PREFIX}/{lib_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()["data"]
    assert data["id"] == lib_id
    assert data["name"] == "Detail Lib"
    for field in ("library_key", "language", "default_confidence_threshold", "created_at", "updated_at"):
        assert field in data


@pytest.mark.asyncio
async def test_update_library(client):
    headers = await _auth_headers(client)

    create_resp = await _create_library(client, headers, name="Before Update")
    assert create_resp.status_code == 201
    lib_id = create_resp.json()["data"]["id"]

    update_resp = await client.put(
        f"{PREFIX}/{lib_id}",
        json={"name": "After Update"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["name"] == "After Update"

    get_resp = await client.get(f"{PREFIX}/{lib_id}", headers=headers)
    assert get_resp.json()["data"]["name"] == "After Update"


@pytest.mark.asyncio
async def test_update_library_language(client):
    """D022: 更新指令库时 language 字段应正确生效"""
    headers = await _auth_headers(client)

    create_resp = await _create_library(client, headers, name="Lang Update Lib", key=_unique_key())
    assert create_resp.status_code == 201
    lib_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["language"] == "zh"

    update_resp = await client.put(
        f"{PREFIX}/{lib_id}",
        json={"language": "en"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["language"] == "en"

    get_resp = await client.get(f"{PREFIX}/{lib_id}", headers=headers)
    assert get_resp.json()["data"]["language"] == "en"


@pytest.mark.asyncio
async def test_delete_library(client):
    headers = await _auth_headers(client)

    create_resp = await _create_library(client, headers, name="To Delete")
    assert create_resp.status_code == 201
    lib_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"{PREFIX}/{lib_id}", headers=headers)
    assert del_resp.status_code == 200

    get_resp = await client.get(f"{PREFIX}/{lib_id}", headers=headers)
    assert get_resp.json()["code"] == "E50102"


@pytest.mark.asyncio
async def test_create_duplicate_key_rejected(client):
    headers = await _auth_headers(client)
    key = _unique_key()

    first = await _create_library(client, headers, key=key)
    assert first.status_code == 201

    second = await _create_library(client, headers, key=key)
    assert second.json()["code"] == "E50101"


@pytest.mark.asyncio
async def test_start_training_model_version(client):
    """D031: POST /models/{id}/train must succeed for draft model (no 500)."""
    headers = await _auth_headers(client)

    create_lib = await _create_library(client, headers, name="Train Flow Lib", key=_unique_key())
    assert create_lib.status_code == 201
    lib_id = create_lib.json()["data"]["id"]

    create_model = await client.post(
        f"{PREFIX}/{lib_id}/models",
        json={"version_name": "v-test-train", "notes": "it"},
        headers=headers,
    )
    assert create_model.status_code == 201, create_model.text
    model_id = create_model.json()["data"]["id"]

    train_body = {
        "base_model": "bert-base-chinese",
        "learning_rate": 0.00002,
        "batch_size": 32,
        "epochs": 10,
        "early_stopping": True,
        "early_stopping_patience": 2,
    }
    train_resp = await client.post(
        f"/api/v1/models/{model_id}/train",
        json=train_body,
        headers=headers,
    )
    assert train_resp.status_code == 200, train_resp.text
    body = train_resp.json()
    assert body["code"] == "000000"
    assert body["data"]["status"] == "training"
    cfg = body["data"]["train_config"]
    assert cfg.get("base_model") == "bert-base-chinese"
    assert cfg.get("epochs") == 10
