"""Contract tests for app.api.v1.intents — intent CRUD routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

DS_ID = str(uuid.uuid4())
INTENT_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.intents.intent_data_service"


@pytest.mark.asyncio
async def test_list_intents_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_intents = AsyncMock(return_value=[
            {"id": INTENT_ID, "intent_key": "greet", "name_zh": "问候"},
        ])
        resp = await client.get(
            f"/api/v1/datasets/{DS_ID}/intents",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_create_intent_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {
        "intent_key": "greet",
        "name_zh": "问候",
        "slot_keys": [],
    }
    with patch(PATCH_SVC) as svc:
        svc.create_intent = AsyncMock(return_value={"id": INTENT_ID, **payload})
        resp = await client.post(
            f"/api/v1/datasets/{DS_ID}/intents",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == INTENT_ID


@pytest.mark.asyncio
async def test_get_intent_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_intent = AsyncMock(return_value={
            "id": INTENT_ID, "intent_key": "greet", "name_zh": "问候",
        })
        resp = await client.get(
            f"/api/v1/intents/{INTENT_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == INTENT_ID


@pytest.mark.asyncio
async def test_update_intent_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name_zh": "问候语"}
    with patch(PATCH_SVC) as svc:
        svc.update_intent = AsyncMock(return_value={
            "id": INTENT_ID, "intent_key": "greet", **payload,
        })
        resp = await client.put(
            f"/api/v1/intents/{INTENT_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name_zh"] == "问候语"


@pytest.mark.asyncio
async def test_delete_intent_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_intent = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/intents/{INTENT_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get(f"/api/v1/datasets/{DS_ID}/intents")
    assert resp.status_code == 401
