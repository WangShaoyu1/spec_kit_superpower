"""RBAC 权限控制集成测试。

验证受限角色无法访问未授权 API，管理员可访问所有 API，无 token 请求返回 403。
"""
import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.models.user import User, Role


@pytest.fixture
async def restricted_role(db_session):
    """创建仅有 intent_management.read 权限的受限角色。"""
    role = Role(
        name="受限角色",
        permissions={"intent_management": {"read": True, "write": False, "delete": False}},
        is_system=False,
    )
    db_session.add(role)
    await db_session.flush()
    return role


@pytest.fixture
async def restricted_user(db_session, restricted_role):
    """创建受限用户，仅具有 intent_management.read 权限。"""
    user = User(
        username="restricted_user",
        password_hash=hash_password("restricted123"),
        display_name="受限用户",
        role_id=restricted_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def restricted_token(restricted_user):
    """受限用户登录获取 token（模拟登录流程）。"""
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(restricted_user.id), "username": restricted_user.username}
    )


@pytest.fixture
async def restricted_headers(restricted_token):
    """受限用户的 Authorization headers。"""
    return {"Authorization": f"Bearer {restricted_token}"}


# ---------------------------------------------------------------------------
# T121 RBAC 测试场景
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_restricted_user_can_get_intents(
    client: AsyncClient, restricted_headers
):
    """受限用户可访问 GET /intents → 200（有 intent_management.read）。"""
    resp = await client.get("/api/v1/intents", headers=restricted_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_restricted_user_cannot_post_intents(
    client: AsyncClient, restricted_headers
):
    """受限用户不能访问 POST /intents → 403（无 write 权限）。"""
    resp = await client.post(
        "/api/v1/intents",
        json={"intent_key": "test_rbac", "display_name": "RBAC测试", "category": "测试"},
        headers=restricted_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_restricted_user_cannot_access_knowledge(
    client: AsyncClient, restricted_headers
):
    """受限用户不能访问 /knowledge → 403（无 knowledge_management 权限）。"""
    resp = await client.get("/api/v1/knowledge/bases", headers=restricted_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_all_apis(client: AsyncClient, auth_headers):
    """管理员可访问所有 API。"""
    # 意图：列表 + 创建
    list_resp = await client.get("/api/v1/intents", headers=auth_headers)
    assert list_resp.status_code == 200

    create_resp = await client.post(
        "/api/v1/intents",
        json={"intent_key": "admin_test", "display_name": "管理员测试", "category": "测试"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    # 知识库：列表
    kb_resp = await client.get("/api/v1/knowledge/bases", headers=auth_headers)
    assert kb_resp.status_code == 200


@pytest.mark.asyncio
async def test_no_token_returns_403(client: AsyncClient):
    """无 token 请求 → 403 或 401（不同 FastAPI 版本可能返回不同）。"""
    resp = await client.get("/api/v1/intents")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_restricted_user_login_and_get_token(
    client: AsyncClient, restricted_user, restricted_headers
):
    """受限用户登录获取 token，并用该 token 成功访问有权限的 API。"""
    # 通过登录 API 获取 token（验证完整登录流程）
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": restricted_user.username, "password": "restricted123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/intents", headers=headers)
    assert resp.status_code == 200
