import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.models import MonitoringAlertEvent, MonitoringAlertRule, RequestLog


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def seed_request_logs(app):
    now = datetime.utcnow()
    with app.state.session_factory() as session:
        session.add_all(
            [
                RequestLog(
                    id="log_001",
                    request_id="req_001",
                    device_id="device_a",
                    session_id="session_a",
                    profile_id=None,
                    route_type="intent",
                    intent_name="device.control",
                    latency_ms=320,
                    is_error=False,
                    accuracy_hit=True,
                    request_json=json.dumps({"text": "设置180度", "version": "v1.0.3", "device_context": {"device_id": "device_a"}}),
                    response_json=json.dumps(
                        {
                            "route": {"type": "intent", "confidence": 0.96},
                            "intent": {"name": "device.control", "confidence": 0.94},
                            "slots": {"temperature": 180},
                            "reply_text": "已设置到180度",
                            "device_context_snapshot": {"page": "cook"},
                        }
                    ),
                    created_at=now - timedelta(minutes=2),
                ),
                RequestLog(
                    id="log_002",
                    request_id="req_002",
                    device_id="device_a",
                    session_id="session_a",
                    profile_id=None,
                    route_type="knowledge",
                    intent_name="knowledge.query",
                    latency_ms=860,
                    is_error=False,
                    accuracy_hit=True,
                    request_json=json.dumps({"text": "红烧肉怎么做", "version": "v1.0.3", "device_context": {"device_id": "device_a"}}),
                    response_json=json.dumps(
                        {
                            "route": {"type": "knowledge", "confidence": 0.91},
                            "intent": {"name": "knowledge.query", "confidence": 0.88},
                            "slots": {},
                            "reply_text": "可以这样做红烧肉",
                            "device_context_snapshot": {"page": "recipe"},
                        }
                    ),
                    created_at=now - timedelta(minutes=1),
                ),
                RequestLog(
                    id="log_003",
                    request_id="req_003",
                    device_id="device_b",
                    session_id="session_b",
                    profile_id=None,
                    route_type="chitchat",
                    intent_name="fallback.chat",
                    latency_ms=1500,
                    is_error=True,
                    accuracy_hit=False,
                    request_json=json.dumps({"text": "今天天气", "version": "v0.9.1", "device_context": {"device_id": "device_b"}}),
                    response_json=json.dumps(
                        {
                            "route": {"type": "chitchat", "confidence": 0.72},
                            "intent": {"name": "fallback.chat", "confidence": 0.67},
                            "slots": {},
                            "reply_text": "我更擅长厨房问题",
                            "device_context_snapshot": {"page": "home"},
                            "error": {"code": "TRACE-001", "message": "fallback path"},
                        }
                    ),
                    created_at=now - timedelta(seconds=30),
                ),
            ]
        )
        rule = MonitoringAlertRule(
            id="rule_001",
            name="准确率下降",
            metric_key="accuracy_drop",
            comparator="lt",
            threshold=0.9,
            window_minutes=5,
            severity="warn",
            enabled=True,
            created_by="user_001",
        )
        session.add(rule)
        session.flush()
        session.add(
            MonitoringAlertEvent(
                id="event_001",
                rule_id="rule_001",
                metric_value=0.72,
                status="open",
                triggered_at=now - timedelta(minutes=1),
                payload_json=json.dumps({"window": "5m", "samples": 3}),
            )
        )
        session.commit()


def test_monitoring_overview_returns_metrics_distribution_and_latest_alerts(client: TestClient, admin_token: str, app):
    seed_request_logs(app)

    response = client.get("/api/v1/monitoring/overview", headers=auth_headers(admin_token))

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["metrics"]["request_count"] == 3
    assert payload["metrics"]["avg_latency_ms"] > 0
    assert payload["metrics"]["p95_latency_ms"] >= payload["metrics"]["avg_latency_ms"]
    assert payload["metrics"]["accuracy_rate"] == 0.6667
    assert payload["route_distribution"][0]["route_type"] == "intent"
    assert payload["latest_alerts"][0]["rule_name"] == "准确率下降"


def test_monitoring_request_logs_support_filters_and_pagination(client: TestClient, admin_token: str, app):
    seed_request_logs(app)

    response = client.get(
        "/api/v1/monitoring/request-logs?device_id=device_a&route=intent&intent=device.control&is_error=false&window=5m&latency_min_ms=300&latency_max_ms=400&page=1&page_size=10",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["pagination"] == {"page": 1, "page_size": 10, "total": 1}
    assert len(payload["items"]) == 1
    assert payload["items"][0]["request_id"] == "req_001"
    assert payload["items"][0]["trace"]["route"]["type"] == "intent"


def test_monitoring_device_sessions_and_trace_detail_return_real_rounds(client: TestClient, admin_token: str, app):
    seed_request_logs(app)

    sessions = client.get(
        "/api/v1/monitoring/device-sessions?device_id=device_a",
        headers=auth_headers(admin_token),
    )
    assert sessions.status_code == 200
    session_payload = sessions.json()["data"]
    assert len(session_payload["items"]) == 1
    assert session_payload["items"][0]["session_id"] == "session_a"
    assert session_payload["items"][0]["turn_count"] == 2
    assert session_payload["items"][0]["version"] == "v1.0.3"

    detail = client.get(
        "/api/v1/monitoring/sessions/session_a",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 200
    detail_payload = detail.json()["data"]
    assert detail_payload["session"]["device_id"] == "device_a"
    assert len(detail_payload["rounds"]) == 2
    assert detail_payload["rounds"][0]["trace"]["intent"]["name"] == "device.control"
    assert "device_context_snapshot" in detail_payload["rounds"][0]["trace"]


def test_monitoring_alert_rules_can_be_created_listed_and_updated(client: TestClient, admin_token: str, app):
    seed_request_logs(app)

    create_response = client.post(
        "/api/v1/monitoring/alert-rules",
        headers=auth_headers(admin_token),
        json={
            "name": "错误率突增",
            "metric_key": "error_rate_spike",
            "comparator": "gt",
            "threshold": 0.15,
            "window_minutes": 5,
            "severity": "critical",
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["data"]["rule"]["metric_key"] == "error_rate_spike"

    list_response = client.get("/api/v1/monitoring/alert-rules", headers=auth_headers(admin_token))
    assert list_response.status_code == 200
    list_payload = list_response.json()["data"]
    assert len(list_payload["rules"]) == 2
    assert list_payload["latest_events"][0]["status"] == "open"

    rule_id = create_response.json()["data"]["rule"]["id"]
    update_response = client.patch(
        f"/api/v1/monitoring/alert-rules/{rule_id}",
        headers=auth_headers(admin_token),
        json={"enabled": False, "threshold": 0.2, "window_minutes": 10, "severity": "warn"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]["rule"]
    assert updated["enabled"] is False
    assert updated["threshold"] == 0.2
