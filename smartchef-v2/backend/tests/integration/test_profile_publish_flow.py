"""Integration tests for Dialog Profile + Publish flow — runs against real DB + Redis."""

import pytest

from tests.integration.conftest import login_as_admin

PROFILES_PREFIX = "/api/v1/profiles"


async def _auth_headers(client) -> dict[str, str]:
    data = await login_as_admin(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_profile(client, headers, *, name: str = "Test Profile"):
    payload = {
        "name": name,
        "description": "Integration test profile",
        "command_threshold": 0.7,
        "route_strategy": "intent_first",
        "session_timeout_min": 10,
    }
    resp = await client.post(PROFILES_PREFIX, json=payload, headers=headers)
    return resp


@pytest.mark.asyncio
async def test_create_and_get_profile(client):
    headers = await _auth_headers(client)

    create_resp = await _create_profile(client, headers, name="My Profile")
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["code"] == "000000"
    profile_id = body["data"]["id"]

    get_resp = await client.get(f"{PROFILES_PREFIX}/{profile_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()["data"]
    assert data["id"] == profile_id
    assert data["name"] == "My Profile"
    for field in ("status", "command_threshold", "route_strategy", "created_at"):
        assert field in data


@pytest.mark.asyncio
async def test_profile_stats(client):
    headers = await _auth_headers(client)

    resp = await client.get(f"{PROFILES_PREFIX}/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    for key in ("total", "draft", "active"):
        assert key in data
        assert isinstance(data[key], int)


@pytest.mark.asyncio
async def test_publish_fails_without_bindings(client):
    headers = await _auth_headers(client)

    create_resp = await _create_profile(client, headers, name="No Bindings Profile")
    assert create_resp.status_code == 201
    profile_id = create_resp.json()["data"]["id"]

    publish_resp = await client.post(
        f"{PROFILES_PREFIX}/{profile_id}/publish",
        headers=headers,
    )
    assert publish_resp.json()["code"] == "E40301"
