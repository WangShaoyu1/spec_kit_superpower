"""Contract tests for app.api.v1.intent_testing routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

MODEL_ID = str(uuid.uuid4())
SESSION_ID = str(uuid.uuid4())
MSG_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.intent_testing.test_session_service"


@pytest.mark.asyncio
async def test_create_test_session_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name": "Test Session"}
    with patch(PATCH_SVC) as svc:
        svc.create_session = AsyncMock(return_value={
            "id": SESSION_ID,
            "model_id": MODEL_ID,
            "name": "Test Session",
            "message_count": 0,
        })
        resp = await client.post(
            f"/api/v1/models/{MODEL_ID}/test-sessions",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == SESSION_ID


@pytest.mark.asyncio
async def test_list_test_sessions_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_sessions = AsyncMock(return_value=[
            {"id": SESSION_ID, "model_id": MODEL_ID, "name": "S1"},
        ])
        resp = await client.get(
            f"/api/v1/models/{MODEL_ID}/test-sessions",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_update_test_session_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name": "Renamed"}
    with patch(PATCH_SVC) as svc:
        svc.update_session = AsyncMock(return_value={
            "id": SESSION_ID, "name": "Renamed", "model_id": MODEL_ID,
        })
        resp = await client.put(
            f"/api/v1/test-sessions/{SESSION_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "Renamed"


@pytest.mark.asyncio
async def test_delete_test_session_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_session = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/test-sessions/{SESSION_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_send_test_message_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"content": "hello"}
    with patch(PATCH_SVC) as svc:
        svc.send_message = AsyncMock(return_value=[
            {"id": MSG_ID, "role": "user", "content": "hello"},
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": "ok",
            },
        ])
        resp = await client.post(
            f"/api/v1/test-sessions/{SESSION_ID}/messages",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_list_test_messages_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_messages = AsyncMock(return_value=(
            [{"id": MSG_ID, "role": "user", "content": "hello"}],
            1,
        ))
        resp = await client.get(
            f"/api/v1/test-sessions/{SESSION_ID}/messages",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["total"] == 1


@pytest.mark.asyncio
async def test_list_messages_page_size_200_ok(client):
    """D044: UI requests page_size=200; must not 422 (max was 100)."""
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_messages = AsyncMock(return_value=([], 0))
        resp = await client.get(
            f"/api/v1/test-sessions/{SESSION_ID}/messages?page=1&page_size=200",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get(f"/api/v1/models/{MODEL_ID}/test-sessions")
    assert resp.status_code == 401
