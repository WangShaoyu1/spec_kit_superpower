import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import MonitoringAlertEvent, MonitoringAlertRule, RequestLog


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def seed_logs(app, *, latency_ms: int = 1500, accuracy_hit: bool = False, is_error: bool = True):
    now = datetime.utcnow()
    with app.state.session_factory() as session:
        session.add_all(
            [
                RequestLog(
                    id="flow_log_001",
                    request_id="flow_req_001",
                    device_id="device_flow",
                    session_id="session_flow",
                    profile_id=None,
                    route_type="intent",
                    intent_name="device.control",
                    latency_ms=latency_ms,
                    is_error=is_error,
                    accuracy_hit=accuracy_hit,
                    request_json=json.dumps({"text": "设置温度", "device_context": {"device_id": "device_flow"}}),
                    response_json=json.dumps(
                        {
                            "route": {"type": "intent", "confidence": 0.92},
                            "intent": {"name": "device.control", "confidence": 0.9},
                            "slots": {"temperature": 180},
                            "reply_text": "好的",
                            "device_context_snapshot": {"page": "cook"},
                        }
                    ),
                    created_at=now - timedelta(seconds=20),
                )
            ]
        )
        session.commit()


def test_alert_rule_evaluation_opens_and_resolves_events(client: TestClient, admin_token: str, app):
    seed_logs(app, latency_ms=1500, accuracy_hit=False, is_error=True)

    create_rule = client.post(
        "/api/v1/monitoring/alert-rules",
        headers=auth_headers(admin_token),
        json={
            "name": "P99 超标",
            "metric_key": "latency_p99_ms",
            "comparator": "gt",
            "threshold": 1000,
            "window_minutes": 5,
            "severity": "critical",
        },
    )
    assert create_rule.status_code == 200
    rule_id = create_rule.json()["data"]["rule"]["id"]

    first_read = client.get("/api/v1/monitoring/alert-rules", headers=auth_headers(admin_token))
    assert first_read.status_code == 200
    payload = first_read.json()["data"]
    assert payload["latest_events"]
    assert payload["latest_events"][0]["rule_id"] == rule_id
    assert payload["latest_events"][0]["status"] == "open"

    with app.state.session_factory() as session:
        log = session.execute(select(RequestLog).where(RequestLog.id == "flow_log_001")).scalar_one()
        log.latency_ms = 600
        session.commit()

    second_read = client.get("/api/v1/monitoring/alert-rules", headers=auth_headers(admin_token))
    assert second_read.status_code == 200

    with app.state.session_factory() as session:
        event = session.execute(
            select(MonitoringAlertEvent).where(MonitoringAlertEvent.rule_id == rule_id).order_by(MonitoringAlertEvent.triggered_at.desc())
        ).scalar_one()
        assert event.status == "resolved"
        assert event.resolved_at is not None


def test_disabled_rule_does_not_create_new_event(client: TestClient, admin_token: str, app):
    seed_logs(app, latency_ms=1700, accuracy_hit=False, is_error=True)

    with app.state.session_factory() as session:
        session.add(
            MonitoringAlertRule(
                id="rule_disabled",
                name="错误率突增",
                metric_key="error_rate_spike",
                comparator="gt",
                threshold=0.5,
                window_minutes=5,
                severity="warn",
                enabled=False,
                created_by="user_001",
            )
        )
        session.commit()

    response = client.get("/api/v1/monitoring/overview", headers=auth_headers(admin_token))
    assert response.status_code == 200

    with app.state.session_factory() as session:
        events = session.execute(select(MonitoringAlertEvent).where(MonitoringAlertEvent.rule_id == "rule_disabled")).scalars().all()
        assert events == []
