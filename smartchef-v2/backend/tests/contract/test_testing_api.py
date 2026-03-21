"""Contract tests for profile test-session and message routes.

Routes under /profiles/{id}/test-sessions are served by app.api.v1.testing.
Routes under /test-sessions/{id}/messages are served by app.api.v1.intent_testing
(registered earlier in main.py and therefore matched first).
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

PROFILE_ID = str(uuid.uuid4())
SESSION_ID = str(uuid.uuid4())
PATCH_PROFILE_SVC = "app.api.v1.testing.profile_test_service"
PATCH_INTENT_SVC = "app.api.v1.intent_testing.test_session_service"


@pytest.mark.asyncio
async def test_create_session_201(client):
    headers = make_auth_header()
    with patch(PATCH_PROFILE_SVC) as svc:
        svc.create_session = AsyncMock(return_value={
            "id": SESSION_ID, "profile_id": PROFILE_ID, "name": "Test",
        })
        resp = await client.post(
            f"/api/v1/profiles/{PROFILE_ID}/test-sessions",
            json={"name": "Test"},
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == SESSION_ID


@pytest.mark.asyncio
async def test_list_sessions_200(client):
    headers = make_auth_header()
    with patch(PATCH_PROFILE_SVC) as svc:
        svc.list_sessions = AsyncMock(return_value=[
            {"id": SESSION_ID, "name": "Test"},
        ])
        resp = await client.get(
            f"/api/v1/profiles/{PROFILE_ID}/test-sessions", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_send_message_200(client):
    headers = make_auth_header(["intent_library_write"])
    with patch(PATCH_INTENT_SVC) as svc:
        svc.send_message = AsyncMock(return_value={
            "id": str(uuid.uuid4()),
            "session_id": SESSION_ID,
            "role": "assistant",
            "content": "好的，我来帮你。",
        })
        resp = await client.post(
            f"/api/v1/test-sessions/{SESSION_ID}/messages",
            json={"content": "你好"},
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["session_id"] == SESSION_ID


@pytest.mark.asyncio
async def test_get_messages_200(client):
    headers = make_auth_header()
    with patch(PATCH_INTENT_SVC) as svc:
        svc.list_messages = AsyncMock(return_value=(
            [{"id": str(uuid.uuid4()), "role": "user", "content": "你好"}],
            1,
        ))
        resp = await client.get(
            f"/api/v1/test-sessions/{SESSION_ID}/messages", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"]["items"], list)


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.post(
        f"/api/v1/profiles/{PROFILE_ID}/test-sessions",
        json={"name": "Test"},
    )
    assert resp.status_code == 401
