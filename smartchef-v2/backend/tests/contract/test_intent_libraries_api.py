"""Contract tests for app.api.v1.intent_libraries routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

LIB_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.intent_libraries.intent_library_service"


@pytest.mark.asyncio
async def test_list_libraries_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_libraries = AsyncMock(return_value=(
            [{"id": LIB_ID, "library_key": "cooking", "name": "Cooking"}],
            1, 1, 0,
        ))
        resp = await client.get("/api/v1/intent-libraries", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["total"] == 1
    assert len(body["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_create_library_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {
        "library_key": "cooking",
        "name": "Cooking",
        "language": "zh",
    }
    with patch(PATCH_SVC) as svc:
        svc.create_library = AsyncMock(return_value={"id": LIB_ID, **payload})
        resp = await client.post(
            "/api/v1/intent-libraries", json=payload, headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == LIB_ID


@pytest.mark.asyncio
async def test_get_library_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_library = AsyncMock(return_value={
            "id": LIB_ID, "library_key": "cooking", "name": "Cooking",
        })
        resp = await client.get(
            f"/api/v1/intent-libraries/{LIB_ID}", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == LIB_ID


@pytest.mark.asyncio
async def test_get_library_404(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_library = AsyncMock(
            side_effect=BusinessException("E50102", "意图库不存在"),
        )
        resp = await client.get(
            f"/api/v1/intent-libraries/{LIB_ID}", headers=headers,
        )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "E50102"


@pytest.mark.asyncio
async def test_delete_library_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_library = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/intent-libraries/{LIB_ID}", headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get("/api/v1/intent-libraries")
    assert resp.status_code == 401
