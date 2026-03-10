"""用户管理 API 合约测试。

覆盖 GET/POST /api/v1/auth/users、GET/POST /api/v1/auth/roles，
以及重复用户名 409、未认证 403 等场景。
"""
import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# T122 用户管理测试场景
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_users(client: AsyncClient, auth_headers):
    """GET /api/v1/auth/users — 列出用户。"""
    resp = await client.get("/api/v1/auth/users", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if len(data) > 0:
        u = data[0]
        assert "id" in u
        assert "username" in u
        assert "display_name" in u
        assert "role_id" in u
        assert "is_active" in u
        assert "created_at" in u
        assert "updated_at" in u


@pytest.mark.asyncio
async def test_post_users_create(client: AsyncClient, auth_headers, admin_role):
    """POST /api/v1/auth/users — 创建用户。"""
    resp = await client.post(
        "/api/v1/auth/users",
        json={
            "username": "newuser001",
            "password": "password123",
            "display_name": "新用户",
            "role_id": str(admin_role.id),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser001"
    assert data["display_name"] == "新用户"
    assert data["role_id"] == str(admin_role.id)
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_get_roles(client: AsyncClient, auth_headers):
    """GET /api/v1/auth/roles — 列出角色。"""
    resp = await client.get("/api/v1/auth/roles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if len(data) > 0:
        r = data[0]
        assert "id" in r
        assert "name" in r
        assert "permissions" in r
        assert "is_system" in r


@pytest.mark.asyncio
async def test_post_roles_create(client: AsyncClient, auth_headers):
    """POST /api/v1/auth/roles — 创建角色。"""
    resp = await client.post(
        "/api/v1/auth/roles",
        json={
            "name": "测试角色",
            "permissions": {"intent_management": {"read": True}},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "测试角色"
    assert data["permissions"] == {"intent_management": {"read": True}}
    assert data["is_system"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_username_returns_409(
    client: AsyncClient, auth_headers, admin_role
):
    """创建重复用户名 → 409。"""
    await client.post(
        "/api/v1/auth/users",
        json={
            "username": "dup_user",
            "password": "password123",
            "display_name": "第一个",
            "role_id": str(admin_role.id),
        },
        headers=auth_headers,
    )
    resp = await client.post(
        "/api/v1/auth/users",
        json={
            "username": "dup_user",
            "password": "password456",
            "display_name": "第二个",
            "role_id": str(admin_role.id),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_users_unauthorized_returns_403(client: AsyncClient):
    """GET /api/v1/auth/users 未认证 → 403 或 401。"""
    resp = await client.get("/api/v1/auth/users")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_roles_unauthorized_returns_403(client: AsyncClient):
    """GET /api/v1/auth/roles 未认证 → 403 或 401。"""
    resp = await client.get("/api/v1/auth/roles")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_post_users_unauthorized_returns_403(client: AsyncClient):
    """POST /api/v1/auth/users 未认证 → 403 或 401。"""
    resp = await client.post(
        "/api/v1/auth/users",
        json={
            "username": "nobody",
            "password": "password123",
            "display_name": "无名",
        },
    )
    assert resp.status_code in (401, 403)
