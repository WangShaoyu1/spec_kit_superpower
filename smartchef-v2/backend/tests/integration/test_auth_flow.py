"""Integration tests for Authentication flow — real DB + Redis."""

import pytest

from tests.integration.conftest import login_as_admin


class TestAuthFlow:
    """Full authentication chain against real database and Redis."""

    async def test_login_success(self, client):
        data = await login_as_admin(client)

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] > 0

        user = data["user"]
        assert user["username"] == "admin"
        assert user["name"]
        assert "id" in user
        assert "role" in user
        assert user["role"]["name"]
        assert isinstance(user["capabilities"], list)
        assert len(user["capabilities"]) > 0

    async def test_login_wrong_password(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword123",
        })
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "E10101"

    async def test_me_endpoint(self, client):
        data = await login_as_admin(client)
        token = data["access_token"]

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        user = resp.json()["data"]
        assert user["username"] == "admin"
        assert "id" in user
        assert "role" in user
        assert isinstance(user["capabilities"], list)

    async def test_refresh_flow(self, client):
        data = await login_as_admin(client)
        refresh_token = data["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200

        refreshed = resp.json()["data"]
        assert "access_token" in refreshed
        assert refreshed["expires_in"] > 0
        assert refreshed["access_token"] != data["access_token"]

    async def test_logout_invalidates_token(self, client):
        data = await login_as_admin(client)
        token = data["access_token"]

        me_before = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_before.status_code == 200

        logout_resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200

        me_after = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_after.status_code == 401
