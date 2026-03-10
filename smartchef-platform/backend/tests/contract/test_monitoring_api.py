"""
监控 API 合约测试（US9 / T108）。

验证监控相关接口的 HTTP 状态码与响应结构。
路径以 monitoring.py 实际路由为准。
"""
import pytest
from httpx import AsyncClient

from app.models.request_log import RequestLog


# ----- 获取监控指标 -----


@pytest.mark.asyncio
async def test_get_monitoring_stats(client: AsyncClient, auth_headers):
    """GET /api/v1/monitoring/stats — 获取监控指标，返回 200 及指标结构。"""
    resp = await client.get("/api/v1/monitoring/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_requests" in data
    assert "avg_latency_ms" in data
    assert "domain_distribution" in data
    assert "unique_devices" in data
    assert "time_range_hours" in data
    assert isinstance(data["total_requests"], int)
    assert isinstance(data["avg_latency_ms"], (int, float))
    assert isinstance(data["domain_distribution"], dict)
    assert isinstance(data["unique_devices"], int)


@pytest.mark.asyncio
async def test_get_monitoring_stats_with_hours(client: AsyncClient, auth_headers):
    """GET /api/v1/monitoring/stats?hours=48 — 支持 hours 参数。"""
    resp = await client.get(
        "/api/v1/monitoring/stats",
        params={"hours": 48},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["time_range_hours"] == 48


# ----- 请求日志查询 -----


@pytest.mark.asyncio
async def test_list_logs(client: AsyncClient, auth_headers):
    """GET /api/v1/monitoring/logs — 查询请求日志，返回 200 及日志数组。"""
    resp = await client.get("/api/v1/monitoring/logs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_logs_filter_by_device_id(client: AsyncClient, auth_headers, db_session):
    """GET /api/v1/monitoring/logs?device_id=xxx — 支持设备 ID 筛选。"""
    # 先插入一条日志便于验证筛选
    log = RequestLog(
        device_id="device_filter_test",
        input_text="加热两分钟",
        domain="command",
        intent="voice_cmd_heat",
        latency_ms=120,
    )
    db_session.add(log)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/monitoring/logs",
        params={"device_id": "device_filter_test"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for item in data:
        assert item["device_id"] == "device_filter_test"
        assert "id" in item
        assert "input_text" in item
        assert "domain" in item
        assert "intent" in item
        assert "latency_ms" in item
        assert "created_at" in item


# ----- 按设备查看日志 -----


@pytest.mark.asyncio
async def test_get_device_history(client: AsyncClient, auth_headers, db_session):
    """GET /api/v1/monitoring/devices/{device_id}/history — 按设备查看历史日志。"""
    device_id = "device_history_test"
    log = RequestLog(
        device_id=device_id,
        input_text="怎么蒸鱼",
        domain="z",
        intent=None,
        latency_ms=80,
    )
    db_session.add(log)
    await db_session.flush()

    resp = await client.get(
        f"/api/v1/monitoring/devices/{device_id}/history",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for item in data:
        assert "id" in item
        assert "input_text" in item
        assert "domain" in item
        assert "intent" in item
        assert "response_text" in item
        assert "latency_ms" in item
        assert "language" in item
        assert "created_at" in item


@pytest.mark.asyncio
async def test_get_device_history_empty(client: AsyncClient, auth_headers):
    """GET /api/v1/monitoring/devices/nonexistent/history — 无数据时返回空数组。"""
    resp = await client.get(
        "/api/v1/monitoring/devices/nonexistent_device_xyz/history",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ----- 告警规则 -----


@pytest.mark.asyncio
async def test_create_alert_rule(client: AsyncClient, auth_headers):
    """POST /api/v1/monitoring/alerts — 创建告警规则，返回 201 及规则信息。"""
    resp = await client.post(
        "/api/v1/monitoring/alerts",
        json={
            "name": "延迟告警",
            "metric_name": "p95_latency",
            "operator": "gt",
            "threshold": 500,
            "duration_minutes": 5,
            "notification_config": {},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "延迟告警"


@pytest.mark.asyncio
async def test_list_alert_rules(client: AsyncClient, auth_headers):
    """GET /api/v1/monitoring/alerts — 列出告警规则，返回 200 及规则数组。"""
    await client.post(
        "/api/v1/monitoring/alerts",
        json={
            "name": "准确率告警",
            "metric_name": "accuracy",
            "operator": "lt",
            "threshold": 0.9,
            "duration_minutes": 10,
            "notification_config": {"email": "admin@example.com"},
        },
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/monitoring/alerts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for item in data:
        assert "id" in item
        assert "name" in item
        assert "metric_name" in item
        assert "operator" in item
        assert "threshold" in item
        assert "duration_minutes" in item
        assert "is_enabled" in item


# ----- 未认证返回 403 -----


@pytest.mark.asyncio
async def test_unauthorized_returns_403(client: AsyncClient):
    """未携带认证头时，监控接口返回 403。"""
    resp = await client.get("/api/v1/monitoring/stats")
    assert resp.status_code == 403

    resp = await client.get("/api/v1/monitoring/logs")
    assert resp.status_code == 403

    resp = await client.get("/api/v1/monitoring/devices/abc/history")
    assert resp.status_code == 403

    resp = await client.get("/api/v1/monitoring/alerts")
    assert resp.status_code == 403

    resp = await client.post(
        "/api/v1/monitoring/alerts",
        json={
            "name": "x",
            "metric_name": "error_rate",
            "operator": "gt",
            "threshold": 0.1,
            "duration_minutes": 5,
            "notification_config": {},
        },
    )
    assert resp.status_code == 403
