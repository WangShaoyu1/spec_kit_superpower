"""Contract tests for monitoring, alert-rules, and alert-events endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.monitoring import DashboardMetrics, TrendPoint
from tests.contract.conftest import make_auth_header

_MONITOR = make_auth_header(["monitoring_read"])
_ALERT = make_auth_header(["monitoring_manage"])


@pytest.fixture(autouse=True)
def _mock_redis():
    """Prevent RuntimeError from uninitialised Redis in dashboard endpoints."""
    with patch("app.api.v1.monitoring.get_redis", return_value=MagicMock()):
        yield


@pytest.mark.asyncio
async def test_dashboard_200(client):
    with patch("app.api.v1.monitoring.metrics_service") as svc:
        svc.get_dashboard_metrics = AsyncMock(return_value=DashboardMetrics(
            request_count=100, success_rate=99.5,
            avg_latency=42, p99_latency=180,
            active_alerts=0, domain_distribution=[],
        ))
        resp = await client.get("/api/v1/monitoring/dashboard", headers=_MONITOR)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["request_count"] == 100
    assert body["data"]["success_rate"] == 99.5


@pytest.mark.asyncio
async def test_dashboard_trend_200(client):
    with patch("app.api.v1.monitoring.metrics_service") as svc:
        svc.get_trend_data = AsyncMock(return_value=[
            TrendPoint(time_bucket="2025-01-01T00:00", request_count=10, error_count=1, avg_latency=50),
        ])
        resp = await client.get("/api/v1/monitoring/dashboard/trend", headers=_MONITOR)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 1
    assert body["data"][0]["request_count"] == 10


@pytest.mark.asyncio
async def test_query_logs_200(client):
    with patch("app.api.v1.monitoring.log_service") as svc:
        svc.query_logs = AsyncMock(return_value={
            "items": [], "total": 0, "page": 1, "page_size": 20,
        })
        resp = await client.get("/api/v1/monitoring/logs", headers=_MONITOR)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_alert_rules_200(client):
    with patch("app.api.v1.monitoring.alert_service") as svc:
        svc.list_rules = AsyncMock(return_value={
            "items": [], "total": 0, "page": 1, "page_size": 20,
        })
        resp = await client.get("/api/v1/alert-rules", headers=_ALERT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["items"] == []


@pytest.mark.asyncio
async def test_create_alert_rule_200(client):
    rule_data = {
        "id": str(uuid.uuid4()),
        "name": "Latency Alert",
        "metric": "avg_latency",
        "operator": "gt",
        "threshold": 500.0,
        "window_minutes": 5,
        "is_enabled": True,
        "notification_channels": [],
    }
    with patch("app.api.v1.monitoring.alert_service") as svc:
        svc.create_rule = AsyncMock(return_value=rule_data)
        resp = await client.post("/api/v1/alert-rules", json={
            "name": "Latency Alert",
            "metric": "avg_latency",
            "operator": "gt",
            "threshold": 500.0,
            "window_minutes": 5,
        }, headers=_ALERT)
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "Latency Alert"


@pytest.mark.asyncio
async def test_list_alert_events_200(client):
    with patch("app.api.v1.monitoring.alert_service") as svc:
        svc.list_events = AsyncMock(return_value={
            "items": [], "total": 0, "page": 1, "page_size": 20,
        })
        resp = await client.get("/api/v1/alert-events", headers=_ALERT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["items"] == []


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get("/api/v1/monitoring/dashboard")
    assert resp.status_code == 401

    resp = await client.get("/api/v1/monitoring/logs")
    assert resp.status_code == 401

    resp = await client.get("/api/v1/alert-rules")
    assert resp.status_code == 401
