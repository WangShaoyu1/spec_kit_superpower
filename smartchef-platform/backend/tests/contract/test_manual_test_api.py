"""手动测试 API 合约测试。

验证 POST /api/v1/test/sessions 和 POST /api/v1/test/chat 的
HTTP 状态码、响应 JSON 结构、字段存在性。NLU Pipeline 已 mock。
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


# Mock NLU pipeline 返回的 debug_info 结构（路由/意图/槽位/耗时等）
MOCK_DEBUG_INFO = {
    "routing": {"domain": "command", "confidence": 0.95},
    "intent": {"intent_key": "voice_cmd_start_cooking", "confidence": 0.9},
    "slots": [{"key": "duration", "value": "3分钟"}],
    "dialog_state": {"state": "IDLE", "is_complete": True},
    "latency_ms": 120,
}


@pytest.fixture
def mock_run_pipeline():
    """Mock NLU run_pipeline，避免实际调用 LLM/意图分类等。"""
    from app.services.nlu.pipeline import PipelineResult

    async def _fake_run(*args, **kwargs):
        return PipelineResult(
            domain="command",
            route_confidence=0.95,
            intent="voice_cmd_start_cooking",
            intent_confidence=0.9,
            slots={"duration": "3分钟"},
            response_text="好的，启动烹饪（duration=3分钟）",
            needs_followup=False,
            language="zh",
            latency_ms=120,
            debug_info=MOCK_DEBUG_INFO,
        )

    with patch("app.services.testing.manual_test.run_pipeline", new_callable=AsyncMock, side_effect=_fake_run) as m:
        yield m


@pytest.mark.asyncio
async def test_create_test_session(client: AsyncClient, auth_headers):
    """POST /api/v1/test/sessions - 创建测试会话，返回 201 及会话信息。"""
    # 先创建对话方案（create_test_session 依赖 profile 存在）
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "测试方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["id"]

    resp = await client.post(
        "/api/v1/test/sessions",
        json={
            "name": "手动测试会话1",
            "profile_id": profile_id,
            "device_context": {"cooking_state": "idle"},
            "notes": "调试用",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "手动测试会话1"
    assert data["profile_id"] == profile_id
    assert data["device_context"] == {"cooking_state": "idle"}
    assert data["notes"] == "调试用"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_session_minimal_body(client: AsyncClient, auth_headers):
    """创建测试会话 - 最小请求体（仅 name、profile_id）。"""
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "最小方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = profile_resp.json()["id"]

    resp = await client.post(
        "/api/v1/test/sessions",
        json={"name": "最小会话", "profile_id": profile_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "最小会话"
    assert data["profile_id"] == profile_id
    assert data["device_context"] is None
    assert data["notes"] is None


@pytest.mark.asyncio
async def test_chat_returns_debug_info(client: AsyncClient, auth_headers, mock_run_pipeline):
    """POST /api/v1/test/chat - 发送消息，响应包含 debug_info（路由/意图/槽位/耗时等）。"""
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "Chat测试方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = profile_resp.json()["id"]

    session_resp = await client.post(
        "/api/v1/test/sessions",
        json={"name": "Chat会话", "profile_id": profile_id},
        headers=auth_headers,
    )
    session_id = session_resp.json()["id"]

    resp = await client.post(
        "/api/v1/test/chat",
        json={"session_id": session_id, "text": "加热3分钟"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # 合约字段
    assert "response_text" in data
    assert "debug_info" in data
    assert data["debug_info"] == MOCK_DEBUG_INFO
    assert data["domain"] == "command"
    assert data["route_confidence"] == 0.95
    assert data["intent"] == "voice_cmd_start_cooking"
    assert data["intent_confidence"] == 0.9
    assert data["slots"] == {"duration": "3分钟"}
    assert data["latency_ms"] == 120
    assert data["language"] == "zh"


@pytest.mark.asyncio
async def test_chat_session_not_found_returns_404(client: AsyncClient, auth_headers):
    """会话不存在时返回 404。"""
    from uuid import uuid4

    fake_session_id = str(uuid4())
    resp = await client.post(
        "/api/v1/test/chat",
        json={"session_id": fake_session_id, "text": "你好"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "测试会话不存在" in data["detail"] or "不存在" in data["detail"]


@pytest.mark.asyncio
async def test_create_session_unauthorized_returns_403(client: AsyncClient):
    """未认证请求创建会话返回 403。"""
    from uuid import uuid4

    resp = await client.post(
        "/api/v1/test/sessions",
        json={
            "name": "未认证会话",
            "profile_id": str(uuid4()),
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_chat_unauthorized_returns_403(client: AsyncClient):
    """未认证请求发送消息返回 403。"""
    from uuid import uuid4

    resp = await client.post(
        "/api/v1/test/chat",
        json={"session_id": str(uuid4()), "text": "你好"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_session_profile_not_found_returns_404(client: AsyncClient, auth_headers):
    """对话方案不存在时创建会话返回 404。"""
    from uuid import uuid4

    resp = await client.post(
        "/api/v1/test/sessions",
        json={
            "name": "无效会话",
            "profile_id": str(uuid4()),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
