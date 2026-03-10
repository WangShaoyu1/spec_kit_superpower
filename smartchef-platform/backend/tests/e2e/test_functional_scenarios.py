"""端到端功能场景测试：与 spec 用户故事验收场景一一对应。

每个 test_* 对应 spec.md 中一条或一组验收场景（Given-When-Then），
通过 API 调用验证功能，不依赖浏览器。运行前需：DB 迁移、init_db（或 conftest 提供 admin）。
"""
import pytest
from httpx import AsyncClient

from app.main import app
from app.core.redis import get_redis


# ---------------------------------------------------------------------------
# 简易 FakeRedis（与 test_pm_workflow 一致，此处内联避免依赖）
# ---------------------------------------------------------------------------
class FakeRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self._store[key] = value

    async def delete(self, *keys: str):
        n = 0
        for k in keys:
            if self._store.pop(k, None) is not None:
                n += 1
        return n

    async def scan(self, cursor: int, match: str | None = None, count: int | None = None):
        keys = [k for k in self._store if (not match or __import__("fnmatch").fnmatch(k, match))]
        return (0, keys)

    async def aclose(self):
        pass


@pytest.fixture
def fake_redis():
    redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: redis
    yield redis
    app.dependency_overrides.pop(get_redis, None)


# ---------------------------------------------------------------------------
# 场景与 spec 验收映射（见 docs/E2E_SCENARIO_MAPPING.md）
# ---------------------------------------------------------------------------

# US1 指令配置管理
@pytest.mark.asyncio
async def test_us1_create_intent_with_slot(client: AsyncClient, auth_headers: dict):
    """US1 验收1: 创建新指令「设置烹饪时间」+ 必填槽位 duration，保存成功且列表可见。"""
    r = await client.post(
        "/api/v1/intents",
        json={
            "intent_key": "set_cooking_time",
            "display_name": "设置烹饪时间",
            "category": "烹饪控制",
            "description": "设置加热时长",
            "slots": [
                {"slot_key": "duration", "display_name": "时长", "entity_type": "time", "is_required": True, "prompt_text": "请问要加热多久？"},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["intent_key"] == "set_cooking_time"
    assert any(s["slot_key"] == "duration" for s in data["slots"])
    r2 = await client.get("/api/v1/intents", headers=auth_headers)
    assert r2.status_code == 200
    items = r2.json().get("items", r2.json()) if isinstance(r2.json(), dict) else r2.json()
    assert any(i.get("intent_key") == "set_cooking_time" for i in (items or []))


@pytest.mark.asyncio
async def test_us1_list_intents_filter_by_category(client: AsyncClient, auth_headers: dict):
    """US1 验收4: 按分类筛选「烹饪控制」，仅显示该类指令。"""
    r = await client.get("/api/v1/intents", params={"category": "烹饪控制"}, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    items = data.get("items", data) if isinstance(data, dict) else data
    for i in (items or []):
        assert i.get("category") == "烹饪控制"


# US2 知识库管理
@pytest.mark.asyncio
async def test_us2_create_knowledge_base_and_list(client: AsyncClient, auth_headers: dict):
    """US2: 创建知识库，列表中可见。"""
    r = await client.post(
        "/api/v1/knowledge/bases",
        json={"name": "菜谱库", "description": "测试菜谱"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    r2 = await client.get("/api/v1/knowledge/bases", headers=auth_headers)
    assert r2.status_code == 200
    assert any(b.get("name") == "菜谱库" for b in (r2.json() or []))


# US3 对话方案
@pytest.mark.asyncio
async def test_us3_create_profile_and_publish(client: AsyncClient, auth_headers: dict, fake_redis):
    """US3 验收1/4: 创建方案并发布，设备切换新版本。"""
    # 先建意图与方案
    ri = await client.post(
        "/api/v1/intents",
        json={"intent_key": "voice_cmd_start_cooking", "display_name": "开始烹饪", "category": "烹饪控制"},
        headers=auth_headers,
    )
    assert ri.status_code == 201
    intent_id = ri.json()["id"]
    rp = await client.post(
        "/api/v1/profiles",
        json={
            "name": "方案A",
            "llm_provider": "gpt-4o-mini",
            "routing_strategy": "command_first",
            "intent_ids": [intent_id],
        },
        headers=auth_headers,
    )
    assert rp.status_code == 201, rp.text
    profile_id = rp.json()["id"]
    rv = await client.post(
        "/api/v1/versions",
        params={"profile_id": profile_id, "version_tag": "v1.0.0-e2e"},
        headers=auth_headers,
    )
    assert rv.status_code == 201
    assert rv.json().get("is_active") is True


# US4 手动测试
@pytest.mark.asyncio
async def test_us4_test_session_and_chat_debug_info(client: AsyncClient, auth_headers: dict, fake_redis):
    """US4 验收1: 创建测试会话，发送消息，返回含调试信息。"""
    ri = await client.post(
        "/api/v1/intents",
        json={"intent_key": "set_cooking_temp", "display_name": "设置温度", "category": "烹饪控制"},
        headers=auth_headers,
    )
    assert ri.status_code == 201
    rp = await client.post(
        "/api/v1/profiles",
        json={"name": "测试方案", "llm_provider": "gpt-4o-mini", "intent_ids": [ri.json()["id"]]},
        headers=auth_headers,
    )
    assert rp.status_code == 201
    rs = await client.post(
        "/api/v1/test/sessions",
        json={"name": "会话1", "profile_id": rp.json()["id"]},
        headers=auth_headers,
    )
    assert rs.status_code == 201
    session_id = rs.json()["id"]
    rc = await client.post(
        "/api/v1/test/chat",
        json={"session_id": session_id, "text": "设置温度180度"},
        headers=auth_headers,
    )
    assert rc.status_code == 200, rc.text
    chat = rc.json()
    assert "response_text" in chat
    assert "domain" in chat or "intent" in chat or "debug_info" in chat


# US10 角色权限
@pytest.mark.asyncio
async def test_us10_update_role_permissions(client: AsyncClient, auth_headers: dict):
    """US10 验收3: 管理员修改角色权限，可 PATCH /auth/roles/:id。"""
    # 先创建非系统角色
    r = await client.post(
        "/api/v1/auth/roles",
        json={"name": "指令编辑员", "permissions": {"intent_management": {"read": True, "write": True}}},
        headers=auth_headers,
    )
    assert r.status_code == 201
    role_id = r.json()["id"]
    r2 = await client.patch(
        f"/api/v1/auth/roles/{role_id}",
        json={"permissions": {"intent_management": {"read": True, "write": True}, "knowledge_management": {"read": True}}},
        headers=auth_headers,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["permissions"].get("knowledge_management", {}).get("read") is True


# US9 监控
@pytest.mark.asyncio
async def test_us9_monitoring_stats_and_logs(client: AsyncClient, auth_headers: dict):
    """US9 验收1/5: 监控仪表盘可拉取 stats 与 logs。"""
    r = await client.get("/api/v1/monitoring/stats", params={"hours": 24}, headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "total_requests" in data or "avg_latency_ms" in data or "domain_distribution" in data
    r2 = await client.get("/api/v1/monitoring/logs", params={"limit": 10}, headers=auth_headers)
    assert r2.status_code == 200


# US8 批量测试
@pytest.mark.asyncio
async def test_us8_batch_test_create_job_and_cases(client: AsyncClient, auth_headers: dict, fake_redis):
    """US8: 创建批量测试任务并获取用例列表。"""
    ri = await client.post(
        "/api/v1/intents",
        json={"intent_key": "voice_cmd_stop_cooking", "display_name": "停止烹饪", "category": "烹饪控制"},
        headers=auth_headers,
    )
    assert ri.status_code == 201
    rp = await client.post(
        "/api/v1/profiles",
        json={"name": "批测方案", "llm_provider": "gpt-4o-mini", "intent_ids": [ri.json()["id"]]},
        headers=auth_headers,
    )
    assert rp.status_code == 201
    rj = await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "E2E批测",
            "profile_id": rp.json()["id"],
            "test_cases": [{"input_text": "关火", "expected_intent": "voice_cmd_stop_cooking", "expected_domain": "command"}],
            "accuracy_threshold": 0.95,
            "latency_threshold_ms": 200,
        },
        headers=auth_headers,
    )
    assert rj.status_code == 201, rj.text
    job_id = rj.json()["id"]
    rc = await client.get(f"/api/v1/batch-test/jobs/{job_id}/cases", headers=auth_headers)
    assert rc.status_code == 200
