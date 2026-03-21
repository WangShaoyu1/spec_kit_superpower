"""Contract tests for Dialog Profile API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

_PROFILE_ID = str(uuid.uuid4())
_PERSONA_ID = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_list_profiles_200(client):
    headers = make_auth_header(["profile_read"])
    with patch("app.api.v1.profiles.profile_service") as mock_ps:
        mock_ps.list_profiles = AsyncMock(return_value=(
            [{"id": _PROFILE_ID, "name": "Default"}], 1,
        ))
        resp = await client.get("/api/v1/profiles", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert "items" in body["data"]
    assert "total" in body["data"]


@pytest.mark.asyncio
async def test_create_profile_201(client):
    headers = make_auth_header(["profile_write"])
    with patch("app.api.v1.profiles.profile_service") as mock_ps:
        mock_ps.create_profile = AsyncMock(return_value={
            "id": _PROFILE_ID, "name": "NewProfile",
        })
        resp = await client.post(
            "/api/v1/profiles",
            json={
                "name": "NewProfile",
                "command_threshold": 0.7,
                "route_strategy": "intent_first",
                "session_timeout_min": 10,
            },
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "NewProfile"


@pytest.mark.asyncio
async def test_get_profile_404(client):
    headers = make_auth_header(["profile_read"])
    with patch("app.api.v1.profiles.profile_service") as mock_ps:
        mock_ps.get_profile = AsyncMock(
            side_effect=BusinessException("E40101", "对话配置不存在", http_status=404),
        )
        resp = await client.get(
            f"/api/v1/profiles/{uuid.uuid4()}",
            headers=headers,
        )
    assert resp.status_code == 404
    assert resp.json()["code"] == "E40101"


@pytest.mark.asyncio
async def test_list_personas_200(client):
    headers = make_auth_header(["profile_read"])
    with patch("app.api.v1.profiles.persona_service") as mock_persona:
        mock_persona.list_personas = AsyncMock(return_value=[
            {"id": _PERSONA_ID, "name": "Friendly Chef"},
        ])
        resp = await client.get(
            f"/api/v1/profiles/{uuid.uuid4()}/personas",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_create_persona_201(client):
    headers = make_auth_header(["profile_write"])
    with patch("app.api.v1.profiles.persona_service") as mock_persona:
        mock_persona.create_persona = AsyncMock(return_value={
            "id": _PERSONA_ID, "name": "Cheerful",
        })
        resp = await client.post(
            f"/api/v1/profiles/{uuid.uuid4()}/personas",
            json={
                "name": "Cheerful",
                "system_prompt": "You are a cheerful cooking assistant.",
                "temperature": 0.8,
                "max_tokens": 1024,
            },
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "Cheerful"


@pytest.mark.asyncio
async def test_activate_persona_200(client):
    headers = make_auth_header(["profile_write"])
    with patch("app.api.v1.profiles.persona_service") as mock_persona:
        mock_persona.activate_persona = AsyncMock(return_value={
            "id": _PERSONA_ID, "is_active": True,
        })
        resp = await client.post(
            f"/api/v1/profiles/{uuid.uuid4()}/personas/{uuid.uuid4()}/activate",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_get_bindings_200(client):
    headers = make_auth_header(["profile_read"])
    with patch("app.api.v1.profiles.binding_service") as mock_bind:
        mock_bind.list_bindings = AsyncMock(return_value=[
            {"library_id": str(uuid.uuid4()), "priority": 0},
        ])
        resp = await client.get(
            f"/api/v1/profiles/{uuid.uuid4()}/intent-libraries",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get("/api/v1/profiles")
    assert resp.status_code == 401
