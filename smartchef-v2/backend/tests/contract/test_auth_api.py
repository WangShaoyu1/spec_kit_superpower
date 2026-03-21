"""Auth API contract tests — verify request/response shape."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from tests.contract.conftest import make_auth_header


@pytest.mark.asyncio
async def test_login_success(client):
    mock_data = {
        "access_token": "mock.access.token",
        "refresh_token": "mock.refresh.token",
        "token_type": "Bearer",
        "expires_in": 1800,
        "user": {
            "id": str(uuid4()),
            "username": "admin",
            "name": "管理员",
            "role": {"id": str(uuid4()), "name": "超级管理员"},
            "capabilities": ["user_manage"],
        },
    }
    with patch("app.api.v1.auth.auth_service") as mock_svc:
        mock_svc.login = AsyncMock(return_value=mock_data)
        resp = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123456",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "Bearer"
    assert "user" in body["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    from app.core.api_response import AuthException
    with patch("app.api.v1.auth.auth_service") as mock_svc:
        mock_svc.login = AsyncMock(
            side_effect=AuthException("E10101", "用户名或密码错误", http_status=401)
        )
        resp = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword1",
        })

    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "E10101"


@pytest.mark.asyncio
async def test_login_missing_fields(client):
    resp = await client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_logout_success(client):
    headers = make_auth_header()
    with patch("app.api.v1.auth.blacklist_token", new_callable=AsyncMock):
        resp = await client.post("/api/v1/auth/logout", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["code"] == "000000"


@pytest.mark.asyncio
async def test_me_success(client):
    headers = make_auth_header()
    mock_user = {
        "id": str(uuid4()),
        "username": "admin",
        "name": "管理员",
        "status": "active",
        "capabilities": ["user_manage"],
    }
    with patch("app.api.v1.auth.auth_service") as mock_svc:
        mock_svc.get_current_user = AsyncMock(return_value=mock_user)
        resp = await client.get("/api/v1/auth/me", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert "id" in body["data"]
    assert "username" in body["data"]


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client):
    mock_data = {
        "access_token": "new.access.token",
        "token_type": "Bearer",
        "expires_in": 1800,
    }
    with patch("app.api.v1.auth.auth_service") as mock_svc:
        mock_svc.refresh_token = AsyncMock(return_value=mock_data)
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "some.refresh.token",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert "access_token" in body["data"]


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    from app.core.api_response import AuthException
    with patch("app.api.v1.auth.auth_service") as mock_svc:
        mock_svc.refresh_token = AsyncMock(
            side_effect=AuthException("E10103", "Refresh Token 无效", http_status=401)
        )
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })

    assert resp.status_code == 401
