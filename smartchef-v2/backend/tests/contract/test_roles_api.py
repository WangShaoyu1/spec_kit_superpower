"""Contract tests for Role and Permission management API.

Covers app.api.v1.roles and app.api.v1.permissions routes.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

ROLE_ID = "00000000-0000-0000-0000-000000000010"

SAMPLE_ROLE = {
    "id": ROLE_ID,
    "name": "Editor",
    "description": "Content editor role",
    "is_builtin": False,
    "user_count": 3,
    "permission_count": 5,
    "created_at": "2025-01-01T00:00:00",
}


@pytest.mark.asyncio
async def test_list_roles_200(client):
    headers = make_auth_header(["role_manage"])

    with patch("app.api.v1.roles.role_service") as mock_svc:
        mock_svc.list_roles = AsyncMock(return_value=[SAMPLE_ROLE])
        resp = await client.get("/api/v1/roles", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Editor"


@pytest.mark.asyncio
async def test_create_role_201(client):
    headers = make_auth_header(["role_manage"])
    payload = {"name": "Reviewer", "description": "Review permissions", "permission_keys": []}

    with patch("app.api.v1.roles.role_service") as mock_svc:
        mock_svc.create_role = AsyncMock(return_value={
            "id": ROLE_ID,
            "name": "Reviewer",
            "description": "Review permissions",
            "is_builtin": False,
            "permission_count": 0,
            "created_at": "2025-01-01T00:00:00",
        })
        resp = await client.post("/api/v1/roles", json=payload, headers=headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "Reviewer"
    assert body["data"]["id"] == ROLE_ID


@pytest.mark.asyncio
async def test_create_role_409_duplicate(client):
    headers = make_auth_header(["role_manage"])
    payload = {"name": "Admin", "description": "Duplicate"}

    with patch("app.api.v1.roles.role_service") as mock_svc:
        mock_svc.create_role = AsyncMock(
            side_effect=BusinessException("E10301", "角色名称已存在", http_status=409)
        )
        resp = await client.post("/api/v1/roles", json=payload, headers=headers)

    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "E10301"
    assert body["data"] is None


@pytest.mark.asyncio
async def test_get_role_404(client):
    headers = make_auth_header(["role_manage"])

    with patch("app.api.v1.roles.role_service") as mock_svc:
        mock_svc.get_role = AsyncMock(
            side_effect=BusinessException("E10302", "角色不存在", http_status=404)
        )
        resp = await client.get(f"/api/v1/roles/{ROLE_ID}", headers=headers)

    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "E10302"


@pytest.mark.asyncio
async def test_delete_role_200(client):
    headers = make_auth_header(["role_manage"])

    with patch("app.api.v1.roles.role_service") as mock_svc:
        mock_svc.delete_role = AsyncMock(return_value=None)
        resp = await client.delete(f"/api/v1/roles/{ROLE_ID}", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_permissions_list_200(client):
    headers = make_auth_header(["role_manage"])

    with patch("app.api.v1.permissions.role_service") as mock_svc:
        mock_svc.get_all_permissions = AsyncMock(return_value=[
            {
                "module": "系统",
                "permissions": [
                    {"key": "user_manage", "label": "用户管理"},
                    {"key": "role_manage", "label": "角色管理"},
                ],
            }
        ])
        resp = await client.get("/api/v1/permissions", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)
    assert body["data"][0]["module"] == "系统"
    assert len(body["data"][0]["permissions"]) == 2
