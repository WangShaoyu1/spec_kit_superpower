"""Contract tests for User management API (app.api.v1.users).

Verify HTTP request/response shape by mocking the service layer.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

USER_ID = "00000000-0000-0000-0000-000000000099"
ROLE_ID = "00000000-0000-0000-0000-000000000002"

SAMPLE_USER = {
    "id": USER_ID,
    "username": "testuser",
    "name": "Test User",
    "status": "active",
    "is_builtin": False,
    "role": {"id": ROLE_ID, "name": "Admin"},
    "capabilities": ["user_manage"],
    "last_login_at": None,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": None,
}


@pytest.mark.asyncio
async def test_list_users_200(client):
    headers = make_auth_header(["user_manage"])

    with patch("app.api.v1.users.user_service") as mock_svc:
        mock_svc.list_users = AsyncMock(return_value={
            "items": [SAMPLE_USER],
            "total": 1,
            "page": 1,
            "page_size": 20,
        })
        resp = await client.get("/api/v1/users", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["msg"] == "success"
    data = body["data"]
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == "testuser"


@pytest.mark.asyncio
async def test_create_user_201(client):
    headers = make_auth_header(["user_manage"])
    payload = {
        "username": "newuser",
        "name": "New User",
        "password": "Passw0rd123",
        "role_id": ROLE_ID,
    }

    with patch("app.api.v1.users.user_service") as mock_svc:
        mock_svc.create_user = AsyncMock(return_value={
            "id": USER_ID,
            "username": "newuser",
            "name": "New User",
            "status": "active",
            "role": {"id": ROLE_ID, "name": "Admin"},
            "created_at": "2025-01-01T00:00:00",
        })
        resp = await client.post("/api/v1/users", json=payload, headers=headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["username"] == "newuser"
    assert body["data"]["id"] == USER_ID


@pytest.mark.asyncio
async def test_create_user_409_duplicate(client):
    headers = make_auth_header(["user_manage"])
    payload = {
        "username": "dupuser",
        "name": "Dup User",
        "password": "Passw0rd123",
        "role_id": ROLE_ID,
    }

    with patch("app.api.v1.users.user_service") as mock_svc:
        mock_svc.create_user = AsyncMock(
            side_effect=BusinessException("E10201", "用户名已存在", http_status=409)
        )
        resp = await client.post("/api/v1/users", json=payload, headers=headers)

    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "E10201"
    assert body["data"] is None


@pytest.mark.asyncio
async def test_get_user_200(client):
    headers = make_auth_header(["user_manage"])

    with patch("app.api.v1.users.user_service") as mock_svc:
        mock_svc.get_user = AsyncMock(return_value=SAMPLE_USER)
        resp = await client.get(f"/api/v1/users/{USER_ID}", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == USER_ID
    assert body["data"]["username"] == "testuser"
    assert "role" in body["data"]


@pytest.mark.asyncio
async def test_get_user_404(client):
    headers = make_auth_header(["user_manage"])

    with patch("app.api.v1.users.user_service") as mock_svc:
        mock_svc.get_user = AsyncMock(
            side_effect=BusinessException("E10202", "用户不存在", http_status=404)
        )
        resp = await client.get(f"/api/v1/users/{USER_ID}", headers=headers)

    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "E10202"


@pytest.mark.asyncio
async def test_delete_user_200(client):
    headers = make_auth_header(["user_manage"])

    with patch("app.api.v1.users.user_service") as mock_svc:
        mock_svc.delete_user = AsyncMock(return_value=None)
        resp = await client.delete(f"/api/v1/users/{USER_ID}", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get("/api/v1/users")

    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "E10102"
