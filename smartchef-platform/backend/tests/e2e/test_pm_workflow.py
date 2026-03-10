"""端到端验收测试：模拟 PM 全流程（创建方案 → 测试 → 发布 → 设备调用）。

验证 SC-007 时效约束：
  PM 从创建对话方案到完成手动测试并发布版本，整个流程可在 1 小时内完成。
验证 SC-002 时效约束：
  /dialog/chat 响应延迟 < 200ms（mock 外部依赖后验证 API 层延迟）。

Mock 策略：
  - ONNX 模型推理 → mock classify_intent
  - LLM 调用 → mock chat_completion
  - 知识库问答 → mock generate_knowledge_answer
  - Web 搜索 → mock needs_web_search
  - Redis → 内存 FakeRedis
  - 保持 API 层路由、数据库交互完全真实
"""

import fnmatch
import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.redis import get_redis
from app.main import app
from app.services.nlu.intent_classifier import IntentResult


# ---------------------------------------------------------------------------
# FakeRedis：内存实现，替代真实 Redis 连接
# ---------------------------------------------------------------------------
class FakeRedis:
    """支持 device_session / clear_all_sessions 所需操作的内存 Redis。"""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if self._store.pop(k, None) is not None:
                count += 1
        return count

    async def scan(
        self, cursor: int, match: str | None = None, count: int | None = None,
    ) -> tuple[int, list[str]]:
        if match:
            keys = [k for k in self._store if fnmatch.fnmatch(k, match)]
        else:
            keys = list(self._store.keys())
        return (0, keys)

    async def aclose(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def fake_redis():
    """注入 FakeRedis 到 FastAPI 依赖，测试结束后清理。"""
    redis = FakeRedis()

    async def _override():
        return redis

    app.dependency_overrides[get_redis] = _override
    yield redis
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture()
def mock_nlu_externals():
    """Mock 所有外部依赖（ONNX / LLM / 知识库 / Web 搜索），保持 API 层真实。

    各测试函数可通过返回的字典进一步配置 mock 行为。
    """
    with (
        patch(
            "app.services.nlu.pipeline.classify_intent",
            new_callable=AsyncMock,
        ) as mock_classify,
        patch(
            "app.services.nlu.pipeline.chat_completion",
            new_callable=AsyncMock,
            return_value="好的，我来帮您处理。",
        ) as mock_llm,
        patch(
            "app.services.nlu.pipeline.needs_web_search",
            return_value=False,
        ) as mock_ws,
        patch(
            "app.services.nlu.pipeline.generate_knowledge_answer",
            new_callable=AsyncMock,
            return_value=("", []),
        ) as mock_kb,
    ):
        yield {
            "classify_intent": mock_classify,
            "chat_completion": mock_llm,
            "needs_web_search": mock_ws,
            "generate_knowledge_answer": mock_kb,
        }


# ---------------------------------------------------------------------------
# 时效约束阈值
# ---------------------------------------------------------------------------
DEVICE_CHAT_LATENCY_THRESHOLD_MS = 200  # SC-002: API 层延迟上限
WORKFLOW_TIMEOUT_MS = 60_000  # 保守阈值（远低于 SC-007 的 1 小时）


# ===========================================================================
# 测试用例
# ===========================================================================


@pytest.mark.asyncio
async def test_pm_full_workflow(
    client: AsyncClient,
    auth_headers: dict,
    fake_redis: FakeRedis,
    mock_nlu_externals: dict,
):
    """SC-007 验收：模拟 PM 完整工作流。

    步骤：
      1. 创建意图配置
      2. 添加训练数据
      3. 创建对话方案
      4. 创建手动测试会话
      5. 发送测试消息并验证识别结果
      6. 发布版本
      7. 通过设备端 API 调用并验证响应
      8. 验证时效约束
    """
    timings: dict[str, float] = {}
    workflow_start = time.perf_counter()

    # -- 配置 NLU mock：模拟 ONNX 推理结果 --
    mock_nlu_externals["classify_intent"].return_value = IntentResult(
        intent_key="voice_cmd_start_cooking",
        confidence=0.95,
        top_k=[{"intent_key": "voice_cmd_start_cooking", "confidence": 0.95}],
    )

    # ================================================================
    # 步骤 1：创建意图配置（POST /api/v1/intents）
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        "/api/v1/intents",
        json={
            "intent_key": "voice_cmd_start_cooking",
            "display_name": "启动烹饪",
            "category": "烹饪控制",
            "description": "启动微波炉开始烹饪",
            "slots": [
                {
                    "slot_key": "duration",
                    "display_name": "时长",
                    "entity_type": "time",
                    "is_required": True,
                    "prompt_text": "请问您要加热多长时间？",
                },
            ],
        },
        headers=auth_headers,
    )
    timings["1_create_intent"] = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 201, f"创建意图失败: {resp.text}"
    intent_data = resp.json()
    intent_id = intent_data["id"]
    assert intent_data["intent_key"] == "voice_cmd_start_cooking"
    assert len(intent_data["slots"]) == 1
    assert intent_data["slots"][0]["slot_key"] == "duration"

    # ================================================================
    # 步骤 2：添加训练数据（POST /api/v1/intents/{id}/training-data/batch）
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        f"/api/v1/intents/{intent_id}/training-data/batch",
        json=[
            {"text": "开始烹饪"},
            {"text": "启动微波炉"},
            {"text": "开始加热"},
            {"text": "启动烹饪"},
        ],
        headers=auth_headers,
    )
    timings["2_add_training_data"] = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 201, f"添加训练数据失败: {resp.text}"
    assert len(resp.json()) == 4

    # ================================================================
    # 步骤 3：创建对话方案（POST /api/v1/profiles）
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        "/api/v1/profiles",
        json={
            "name": "E2E 验收测试方案",
            "description": "端到端验收测试使用的对话方案",
            "llm_provider": "gpt-4o-mini",
            "llm_config": {"temperature": 0.7},
            "routing_strategy": "command_first",
            "session_timeout_minutes": 10,
            "intent_ids": [intent_id],
        },
        headers=auth_headers,
    )
    timings["3_create_profile"] = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 201, f"创建对话方案失败: {resp.text}"
    profile_data = resp.json()
    profile_id = profile_data["id"]
    assert profile_data["name"] == "E2E 验收测试方案"
    assert profile_data["routing_strategy"] == "command_first"

    # ================================================================
    # 步骤 4：创建手动测试会话（POST /api/v1/test/sessions）
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        "/api/v1/test/sessions",
        json={
            "name": "PM 验收测试会话",
            "profile_id": profile_id,
            "notes": "SC-007 端到端验收测试",
        },
        headers=auth_headers,
    )
    timings["4_create_test_session"] = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 201, f"创建测试会话失败: {resp.text}"
    session_data = resp.json()
    test_session_id = session_data["id"]
    assert session_data["profile_id"] == profile_id

    # ================================================================
    # 步骤 5：发送测试消息（POST /api/v1/test/chat）
    #   指令类输入 "开始烹饪5分钟"，期望识别为 voice_cmd_start_cooking
    #   槽位 duration 应通过正则提取器提取出 "5"
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        "/api/v1/test/chat",
        json={
            "session_id": test_session_id,
            "text": "开始烹饪5分钟",
        },
        headers=auth_headers,
    )
    timings["5_test_chat"] = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200, f"测试消息发送失败: {resp.text}"
    chat_data = resp.json()
    assert chat_data["domain"] == "command", f"预期 command 域，实际: {chat_data['domain']}"
    assert chat_data["intent"] == "voice_cmd_start_cooking"
    assert chat_data["response_text"], "回复内容不应为空"

    # ================================================================
    # 步骤 6：发布版本（POST /api/v1/versions）
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        "/api/v1/versions",
        params={
            "profile_id": profile_id,
            "version_tag": "v1.0.0-e2e",
            "description": "E2E 测试发布版本",
        },
        headers=auth_headers,
    )
    timings["6_publish_version"] = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 201, f"发布版本失败: {resp.text}"
    version_data = resp.json()
    assert version_data["is_active"] is True
    assert version_data["version_tag"] == "v1.0.0-e2e"

    # ================================================================
    # 步骤 7：设备端 API 调用（POST /api/v1/dialog/chat）
    #   模拟真实设备发送语音指令，验证端到端响应正确
    # ================================================================
    t0 = time.perf_counter()
    resp = await client.post(
        "/api/v1/dialog/chat",
        json={
            "device_id": "e2e-test-device-001",
            "text": "启动烹饪3分钟",
            "language": "zh",
        },
    )
    device_chat_ms = (time.perf_counter() - t0) * 1000
    timings["7_device_chat"] = device_chat_ms
    assert resp.status_code == 200, f"设备端调用失败: {resp.text}"
    device_data = resp.json()
    assert device_data["domain"] == "command"
    assert device_data["intent"] == "voice_cmd_start_cooking"
    assert device_data["response_text"], "设备端回复不应为空"
    assert device_data["session_id"], "设备会话应已建立"

    # ================================================================
    # 步骤 8：验证 SC-007 / SC-002 时效约束
    # ================================================================
    workflow_total_ms = (time.perf_counter() - workflow_start) * 1000

    # SC-007: 全流程应在合理时间内完成（实际 API 测试远低于 1 小时上限）
    assert workflow_total_ms < WORKFLOW_TIMEOUT_MS, (
        f"SC-007 违规：全流程耗时 {workflow_total_ms:.0f}ms，超过 {WORKFLOW_TIMEOUT_MS}ms 阈值"
    )

    # SC-002: /dialog/chat API 层延迟 < 200ms（已 mock 外部依赖）
    assert device_chat_ms < DEVICE_CHAT_LATENCY_THRESHOLD_MS, (
        f"SC-002 违规：/dialog/chat 延迟 {device_chat_ms:.0f}ms，"
        f"超过 {DEVICE_CHAT_LATENCY_THRESHOLD_MS}ms 阈值"
    )

    # 打印各步骤耗时（方便 CI 日志排查）
    print("\n=== SC-007 PM 全流程各步骤耗时 ===")
    for step, ms in timings.items():
        print(f"  {step}: {ms:.1f}ms")
    print(f"  总耗时: {workflow_total_ms:.1f}ms")


@pytest.mark.asyncio
async def test_device_chat_latency_p95(
    client: AsyncClient,
    auth_headers: dict,
    fake_redis: FakeRedis,
    mock_nlu_externals: dict,
):
    """SC-002 补充验证：多次调用 /dialog/chat 取 P95 延迟。

    排除单次测量波动，以统计方式验证 API 层延迟稳定低于阈值。
    """
    # -- 配置 NLU mock：无槽位的简单意图 --
    mock_nlu_externals["classify_intent"].return_value = IntentResult(
        intent_key="voice_cmd_pause",
        confidence=0.92,
        top_k=[{"intent_key": "voice_cmd_pause", "confidence": 0.92}],
    )

    # 前置：创建意图 + 方案 + 发布版本
    resp = await client.post(
        "/api/v1/intents",
        json={
            "intent_key": "voice_cmd_pause",
            "display_name": "暂停烹饪",
            "category": "烹饪控制",
            "description": "暂停当前烹饪任务",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"创建意图失败: {resp.text}"
    intent_id = resp.json()["id"]

    resp = await client.post(
        "/api/v1/profiles",
        json={
            "name": "延迟测试方案",
            "llm_provider": "gpt-4o-mini",
            "intent_ids": [intent_id],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"创建方案失败: {resp.text}"
    profile_id = resp.json()["id"]

    resp = await client.post(
        "/api/v1/versions",
        params={"profile_id": profile_id, "version_tag": "v-latency-test"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"发布版本失败: {resp.text}"

    # 多次调用测量延迟
    num_calls = 5
    latencies: list[float] = []
    for i in range(num_calls):
        t0 = time.perf_counter()
        resp = await client.post(
            "/api/v1/dialog/chat",
            json={
                "device_id": f"latency-device-{i:03d}",
                "text": "暂停",
                "language": "zh",
            },
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)
        assert resp.status_code == 200, f"第 {i+1} 次调用失败: {resp.text}"

    avg_ms = sum(latencies) / len(latencies)
    p95_idx = int(len(latencies) * 0.95)
    p95_ms = sorted(latencies)[min(p95_idx, len(latencies) - 1)]

    print(f"\n=== SC-002 延迟统计（{num_calls} 次调用）===")
    print(f"  平均: {avg_ms:.1f}ms | P95: {p95_ms:.1f}ms")
    print(f"  各次: {', '.join(f'{l:.1f}' for l in latencies)}ms")

    assert p95_ms < DEVICE_CHAT_LATENCY_THRESHOLD_MS, (
        f"SC-002 违规：P95 延迟 {p95_ms:.0f}ms，"
        f"超过 {DEVICE_CHAT_LATENCY_THRESHOLD_MS}ms 阈值"
    )


@pytest.mark.asyncio
async def test_workflow_version_activation(
    client: AsyncClient,
    auth_headers: dict,
    fake_redis: FakeRedis,
    mock_nlu_externals: dict,
):
    """验证版本发布后设备端可正确获取激活版本信息。

    补充场景：PM 发布后通过 /dialog/version 确认设备端可感知新版本。
    """
    mock_nlu_externals["classify_intent"].return_value = IntentResult(
        intent_key="voice_cmd_start_cooking",
        confidence=0.95,
        top_k=[{"intent_key": "voice_cmd_start_cooking", "confidence": 0.95}],
    )

    # 创建最小数据集
    resp = await client.post(
        "/api/v1/intents",
        json={
            "intent_key": "voice_cmd_start_cooking",
            "display_name": "启动烹饪",
            "category": "烹饪控制",
            "slots": [
                {
                    "slot_key": "duration",
                    "display_name": "时长",
                    "entity_type": "time",
                    "is_required": True,
                    "prompt_text": "请问您要加热多长时间？",
                },
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    intent_id = resp.json()["id"]

    resp = await client.post(
        "/api/v1/profiles",
        json={
            "name": "版本激活测试方案",
            "llm_provider": "gpt-4o-mini",
            "intent_ids": [intent_id],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    profile_id = resp.json()["id"]

    # 发布前：设备端应无激活版本
    resp = await client.get("/api/v1/dialog/version")
    assert resp.status_code == 200
    assert resp.json()["active"] is False

    # 发布版本
    resp = await client.post(
        "/api/v1/versions",
        params={
            "profile_id": profile_id,
            "version_tag": "v2.0.0-activation",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    # 发布后：设备端应感知到激活版本
    resp = await client.get("/api/v1/dialog/version")
    assert resp.status_code == 200
    version_info = resp.json()
    assert version_info["active"] is True
    assert version_info["version_tag"] == "v2.0.0-activation"
    assert version_info["profile_id"] == profile_id

    # 设备端调用应能正常响应
    resp = await client.post(
        "/api/v1/dialog/chat",
        json={
            "device_id": "activation-test-device",
            "text": "开始烹饪10分钟",
            "language": "zh",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "command"
    assert data["intent"] == "voice_cmd_start_cooking"
