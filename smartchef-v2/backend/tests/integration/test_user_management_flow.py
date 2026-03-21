"""Integration tests for User Management CRUD — real DB + Redis."""

import uuid

import pytest

from tests.integration.conftest import login_as_admin

_SUFFIX = uuid.uuid4().hex[:8]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestUserManagementFlow:
    """User CRUD with role assignment against real database."""

    async def test_full_user_lifecycle(self, client):
        """create → get → update name → disable → delete"""
        admin = await login_as_admin(client)
        headers = _auth_header(admin["access_token"])
        role_id = admin["user"]["role"]["id"]

        # --- create ---
        create_resp = await client.post("/api/v1/users", headers=headers, json={
            "username": f"lifecycle_{_SUFFIX}",
            "name": "Lifecycle User",
            "password": "Test1234pass",
            "role_id": role_id,
        })
        assert create_resp.status_code == 201, create_resp.text
        created = create_resp.json()["data"]
        user_id = created["id"]
        assert created["username"] == f"lifecycle_{_SUFFIX}"
        assert created["name"] == "Lifecycle User"
        assert created["status"] == "active"

        # --- get ---
        get_resp = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert get_resp.status_code == 200
        fetched = get_resp.json()["data"]
        assert fetched["username"] == f"lifecycle_{_SUFFIX}"

        # --- update name ---
        update_resp = await client.put(f"/api/v1/users/{user_id}", headers=headers, json={
            "name": "Updated Name",
        })
        assert update_resp.status_code == 200
        updated = update_resp.json()["data"]
        assert updated["name"] == "Updated Name"

        # --- disable ---
        disable_resp = await client.put(f"/api/v1/users/{user_id}", headers=headers, json={
            "status": "disabled",
        })
        assert disable_resp.status_code == 200
        assert disable_resp.json()["data"]["status"] == "disabled"

        # --- delete (only disabled users can be deleted) ---
        delete_resp = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert delete_resp.status_code == 200

        # --- confirm gone ---
        gone_resp = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert gone_resp.status_code == 404

    async def test_builtin_admin_cannot_be_disabled(self, client):
        admin = await login_as_admin(client)
        headers = _auth_header(admin["access_token"])
        admin_id = admin["user"]["id"]

        resp = await client.put(f"/api/v1/users/{admin_id}", headers=headers, json={
            "status": "disabled",
        })
        assert resp.status_code == 403
        assert resp.json()["code"] == "E10203"

    async def test_create_duplicate_username(self, client):
        admin = await login_as_admin(client)
        headers = _auth_header(admin["access_token"])
        role_id = admin["user"]["role"]["id"]

        payload = {
            "username": f"dupuser_{_SUFFIX}",
            "name": "Dup User",
            "password": "Test1234pass",
            "role_id": role_id,
        }

        first = await client.post("/api/v1/users", headers=headers, json=payload)
        assert first.status_code == 201

        second = await client.post("/api/v1/users", headers=headers, json=payload)
        assert second.status_code == 409
        assert second.json()["code"] == "E10201"

    async def test_role_assignment(self, client):
        admin = await login_as_admin(client)
        headers = _auth_header(admin["access_token"])
        admin_role_id = admin["user"]["role"]["id"]

        # Create a new role (use seeded permission keys from init_db)
        role_resp = await client.post("/api/v1/roles", headers=headers, json={
            "name": f"test_viewer_{_SUFFIX}",
            "description": "Read-only viewer for testing",
            "permission_keys": ["intent_library_read", "profile_read"],
        })
        assert role_resp.status_code == 201, role_resp.text
        new_role_id = role_resp.json()["data"]["id"]

        # Create a user with admin role
        user_resp = await client.post("/api/v1/users", headers=headers, json={
            "username": f"roleuser_{_SUFFIX}",
            "name": "Role Test User",
            "password": "Test1234pass",
            "role_id": admin_role_id,
        })
        assert user_resp.status_code == 201
        user_id = user_resp.json()["data"]["id"]

        # Assign the new role
        assign_resp = await client.put(
            f"/api/v1/users/{user_id}/roles",
            headers=headers,
            json={"role_id": new_role_id},
        )
        assert assign_resp.status_code == 200
        assigned = assign_resp.json()["data"]
        assert assigned["role"]["id"] == new_role_id
        assert assigned["role"]["name"] == f"test_viewer_{_SUFFIX}"
