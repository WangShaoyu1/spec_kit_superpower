"""Contract tests for app.api.v1.versions routes (publish + version management)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

PROFILE_ID = str(uuid.uuid4())
VERSION_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.versions.publisher_service"


@pytest.mark.asyncio
async def test_publish_201(client):
    headers = make_auth_header(["profile_publish"])
    with patch(PATCH_SVC) as svc:
        svc.publish = AsyncMock(return_value={
            "id": VERSION_ID, "profile_id": PROFILE_ID, "version": "v1.0",
        })
        resp = await client.post(
            f"/api/v1/profiles/{PROFILE_ID}/publish", headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == VERSION_ID


@pytest.mark.asyncio
async def test_publish_gate_fail(client):
    headers = make_auth_header(["profile_publish"])
    with patch(PATCH_SVC) as svc:
        svc.publish = AsyncMock(
            side_effect=BusinessException("E40301", "未绑定任何意图库，无法发布"),
        )
        resp = await client.post(
            f"/api/v1/profiles/{PROFILE_ID}/publish", headers=headers,
        )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "E40301"


@pytest.mark.asyncio
async def test_list_versions_200(client):
    headers = make_auth_header(["profile_read"])
    with patch(PATCH_SVC) as svc:
        svc.list_versions = AsyncMock(return_value=[
            {"id": VERSION_ID, "version": "v1.0"},
        ])
        resp = await client.get(
            f"/api/v1/profiles/{PROFILE_ID}/versions", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_get_version_200(client):
    headers = make_auth_header(["profile_read"])
    with patch(PATCH_SVC) as svc:
        svc.get_version = AsyncMock(return_value={
            "id": VERSION_ID, "version": "v1.0", "status": "active",
        })
        resp = await client.get(
            f"/api/v1/versions/{VERSION_ID}", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == VERSION_ID


@pytest.mark.asyncio
async def test_archive_version_200(client):
    headers = make_auth_header(["profile_publish"])
    with patch(PATCH_SVC) as svc:
        svc.archive_version = AsyncMock(return_value={
            "id": VERSION_ID, "status": "archived",
        })
        resp = await client.post(
            f"/api/v1/versions/{VERSION_ID}/archive", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.post(f"/api/v1/profiles/{PROFILE_ID}/publish")
    assert resp.status_code == 401
