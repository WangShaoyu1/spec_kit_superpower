import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_version_check_no_active(client: AsyncClient):
    resp = await client.get("/api/v1/dialog/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is False


@pytest.mark.asyncio
async def test_device_chat_no_active_version(client: AsyncClient):
    resp = await client.post("/api/v1/dialog/chat", json={
        "device_id": "device_001",
        "text": "你好",
        "language": "zh",
    })
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_session_reset(client: AsyncClient):
    resp = await client.post("/api/v1/dialog/reset", params={"device_id": "device_001"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_publish_version(client: AsyncClient, auth_headers):
    profile_resp = await client.post("/api/v1/profiles", json={
        "name": "测试方案", "llm_provider": "gpt-4o",
    }, headers=auth_headers)
    profile_id = profile_resp.json()["id"]

    resp = await client.post("/api/v1/versions", params={
        "profile_id": profile_id,
        "version_tag": "v1.0.0",
        "description": "首次发布",
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["is_active"] is True


@pytest.mark.asyncio
async def test_list_versions(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/versions", headers=auth_headers)
    assert resp.status_code == 200
