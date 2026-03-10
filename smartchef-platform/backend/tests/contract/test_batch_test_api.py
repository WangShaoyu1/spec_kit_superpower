"""批量测试 API 合约测试。

验证 POST/GET /api/v1/batch-test/jobs 及其子资源的
HTTP 状态码、响应 JSON 结构、字段存在性。
批量执行通过 mock run_pipeline 避免实际 NLU 调用。
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from httpx import AsyncClient


# Mock run_pipeline 返回结构，用于快速完成批量执行
MOCK_PIPELINE_RESULT = type(
    "PipelineResult",
    (),
    {
        "domain": "command",
        "route_confidence": 0.95,
        "intent": "voice_cmd_start_cooking",
        "intent_confidence": 0.9,
        "slots": {"duration": "3分钟"},
        "response_text": "好的，启动烹饪（duration=3分钟）",
        "needs_followup": False,
        "language": "zh",
        "latency_ms": 120,
        "debug_info": {"routing": {"domain": "command"}, "intent": {"intent_key": "voice_cmd_start_cooking"}},
    },
)()


@pytest.fixture
def mock_run_pipeline():
    """Mock NLU run_pipeline，批量执行时不调用实际 LLM/意图分类。"""
    async def _fake_run(*args, **kwargs):
        return MOCK_PIPELINE_RESULT

    with patch(
        "app.services.batch_test_service.run_pipeline",
        new_callable=AsyncMock,
        side_effect=_fake_run,
    ) as m:
        yield m


@pytest.mark.asyncio
async def test_post_create_batch_job(client: AsyncClient, auth_headers, mock_run_pipeline):
    """POST /api/v1/batch-test/jobs - 创建并执行批量测试任务，返回 201 及任务信息。"""
    # 先创建对话方案（create 依赖 profile 存在）
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "批量测试方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["id"]

    resp = await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "批量测试任务1",
            "profile_id": profile_id,
            "test_cases": [
                {"input_text": "加热3分钟", "expected_intent": "voice_cmd_start_cooking", "expected_domain": "command"},
                {"input_text": "你好", "expected_domain": "chitchat"},
            ],
            "accuracy_threshold": 0.95,
            "latency_threshold_ms": 200,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "批量测试任务1"
    assert str(data["profile_id"]) == str(profile_id)
    assert data["status"] == "completed"
    assert data["total_cases"] == 2
    assert "passed_cases" in data
    assert "failed_cases" in data
    assert "accuracy" in data
    assert "avg_latency_ms" in data
    assert "report" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_list_batch_jobs(client: AsyncClient, auth_headers, mock_run_pipeline):
    """GET /api/v1/batch-test/jobs - 列出批量测试任务。"""
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "列表方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = profile_resp.json()["id"]

    await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "任务A",
            "profile_id": profile_id,
            "test_cases": [{"input_text": "加热", "expected_intent": "voice_cmd_start_cooking"}],
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "任务B",
            "profile_id": profile_id,
            "test_cases": [{"input_text": "暂停", "expected_intent": "voice_cmd_pause"}],
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/batch-test/jobs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    item = data[0]
    assert "id" in item
    assert "name" in item
    assert "profile_id" in item
    assert "status" in item
    assert "total_cases" in item
    assert "created_at" in item


@pytest.mark.asyncio
async def test_get_job_detail_with_report(client: AsyncClient, auth_headers, mock_run_pipeline):
    """GET /api/v1/batch-test/jobs/{id} - 获取任务详情（含 report）。"""
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "详情方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = profile_resp.json()["id"]

    create_resp = await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "详情任务",
            "profile_id": profile_id,
            "test_cases": [{"input_text": "加热5分钟", "expected_intent": "voice_cmd_start_cooking"}],
        },
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/batch-test/jobs/{job_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["name"] == "详情任务"
    assert "report" in data
    if data["report"]:
        assert "overall_pass" in data["report"] or "accuracy" in data["report"]


@pytest.mark.asyncio
async def test_get_job_cases(client: AsyncClient, auth_headers, mock_run_pipeline):
    """GET /api/v1/batch-test/jobs/{id}/cases - 获取任务用例列表。"""
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"name": "用例方案", "llm_provider": "gpt-4o"},
        headers=auth_headers,
    )
    profile_id = profile_resp.json()["id"]

    create_resp = await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "用例任务",
            "profile_id": profile_id,
            "test_cases": [
                {"input_text": "加热", "expected_intent": "voice_cmd_start_cooking"},
                {"input_text": "暂停", "expected_intent": "voice_cmd_pause"},
            ],
        },
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/batch-test/jobs/{job_id}/cases", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    case = data[0]
    assert "input_text" in case
    assert "expected_intent" in case
    assert "actual_intent" in case
    assert "passed" in case
    assert "latency_ms" in case


@pytest.mark.asyncio
async def test_job_not_found_returns_404(client: AsyncClient, auth_headers):
    """任务不存在时返回 404。"""
    fake_job_id = str(uuid4())
    resp = await client.get(f"/api/v1/batch-test/jobs/{fake_job_id}", headers=auth_headers)
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_job_cases_empty_when_job_not_found(client: AsyncClient, auth_headers):
    """任务不存在时获取用例返回空列表（当前实现行为）。"""
    fake_job_id = str(uuid4())
    resp = await client.get(f"/api/v1/batch-test/jobs/{fake_job_id}/cases", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_job_unauthorized_returns_403(client: AsyncClient):
    """未认证请求创建任务返回 403。"""
    resp = await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "未认证任务",
            "profile_id": str(uuid4()),
            "test_cases": [{"input_text": "测试"}],
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_jobs_unauthorized_returns_403(client: AsyncClient):
    """未认证请求列出任务返回 403。"""
    resp = await client.get("/api/v1/batch-test/jobs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_job_unauthorized_returns_403(client: AsyncClient):
    """未认证请求获取任务详情返回 403。"""
    resp = await client.get(f"/api/v1/batch-test/jobs/{uuid4()}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_job_profile_not_found_returns_404(client: AsyncClient, auth_headers, mock_run_pipeline):
    """对话方案不存在时创建任务返回 404。"""
    resp = await client.post(
        "/api/v1/batch-test/jobs",
        json={
            "name": "无效方案任务",
            "profile_id": str(uuid4()),
            "test_cases": [{"input_text": "测试"}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "方案" in data["detail"] or "存在" in data["detail"]
