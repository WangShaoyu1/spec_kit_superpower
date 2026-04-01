import json
import math
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto import decrypt_json
from app.dependencies import ApiError, create_audit_log, get_db, require_capability, response_envelope
from app.models import MonitoringAlertEvent, MonitoringAlertRule, RequestLog, UserAccount


router = APIRouter(tags=["monitoring"])

WINDOW_TO_MINUTES = {"5m": 5, "15m": 15, "60m": 60}
ALLOWED_METRICS = {"accuracy_drop", "latency_p99_ms", "error_rate_spike"}
ALLOWED_COMPARATORS = {"gt", "gte", "lt", "lte"}
ALLOWED_SEVERITIES = {"info", "warn", "critical"}
ROUTE_ORDER = {"intent": 0, "knowledge": 1, "chitchat": 2, "fallback": 3}


class CreateAlertRulePayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    metric_key: str
    comparator: str
    threshold: float
    window_minutes: int = Field(ge=1, le=1440)
    severity: str


class UpdateAlertRulePayload(BaseModel):
    enabled: bool | None = None
    threshold: float | None = None
    window_minutes: int | None = Field(default=None, ge=1, le=1440)
    severity: str | None = None


def parse_json_field(payload: str | None, fallback: Any):
    if not payload:
        return fallback
    return decrypt_json(payload, fallback)


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat() + "Z"


def percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * ratio) - 1)
    return ordered[index]


def ensure_window_valid(window: str) -> int:
    minutes = WINDOW_TO_MINUTES.get(window)
    if minutes is None:
        raise ApiError(422, "MON-422-WINDOW", "时间窗口参数不合法")
    return minutes


def ensure_metric_valid(metric_key: str):
    if metric_key not in ALLOWED_METRICS:
        raise ApiError(422, "MON-422-METRIC", "指标类型不合法")


def ensure_rule_fields_valid(comparator: str, severity: str, threshold: float):
    if comparator not in ALLOWED_COMPARATORS:
        raise ApiError(422, "MON-422-THRESHOLD", "请检查阈值和比较器")
    if severity not in ALLOWED_SEVERITIES:
        raise ApiError(422, "MON-422-THRESHOLD", "请检查阈值和比较器")
    if threshold < 0:
        raise ApiError(422, "MON-422-THRESHOLD", "请检查阈值和比较器")


def get_rule_or_404(session: Session, rule_id: str) -> MonitoringAlertRule:
    rule = session.get(MonitoringAlertRule, rule_id)
    if rule is None:
        raise ApiError(404, "MON-404-RULE", "目标告警规则不存在")
    return rule


def build_overview_payload(logs: list[RequestLog], latest_alerts: list[dict[str, Any]], window_minutes: int) -> dict[str, Any]:
    latencies = [item.latency_ms for item in logs]
    accuracy_values = [1.0 if item.accuracy_hit else 0.0 for item in logs if item.accuracy_hit is not None]
    route_counts: dict[str, int] = {}
    for item in logs:
        route_counts[item.route_type] = route_counts.get(item.route_type, 0) + 1

    request_count = len(logs)
    metrics = {
        "request_count": request_count,
        "qps": round(request_count / (window_minutes * 60), 4) if request_count else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
        "p95_latency_ms": percentile(latencies, 0.95),
        "p99_latency_ms": percentile(latencies, 0.99),
        "accuracy_rate": round(sum(accuracy_values) / len(accuracy_values), 4) if accuracy_values else None,
        "error_rate": round(sum(1 for item in logs if item.is_error) / request_count, 4) if request_count else 0,
        "average_turns": round(request_count / len({item.session_id for item in logs}), 2) if request_count else 0,
    }
    route_distribution = [
        {"route_type": route_type, "count": count, "ratio": round(count / request_count, 4) if request_count else 0}
        for route_type, count in sorted(route_counts.items(), key=lambda item: (-item[1], ROUTE_ORDER.get(item[0], 99), item[0]))
    ]
    return {
        "metrics": metrics,
        "route_distribution": route_distribution,
        "latest_alerts": latest_alerts,
    }


def serialize_request_log(item: RequestLog) -> dict[str, Any]:
    request_payload = parse_json_field(item.request_json, {})
    trace_payload = parse_json_field(item.response_json, {})
    return {
        "id": item.id,
        "request_id": item.request_id,
        "device_id": item.device_id,
        "session_id": item.session_id,
        "route_type": item.route_type,
        "intent_name": item.intent_name,
        "latency_ms": item.latency_ms,
        "is_error": item.is_error,
        "created_at": serialize_datetime(item.created_at),
        "request": request_payload,
        "trace": trace_payload,
    }


def serialize_alert_rule(rule: MonitoringAlertRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "name": rule.name,
        "metric_key": rule.metric_key,
        "comparator": rule.comparator,
        "threshold": rule.threshold,
        "window_minutes": rule.window_minutes,
        "severity": rule.severity,
        "enabled": rule.enabled,
        "created_by": rule.created_by,
        "created_at": serialize_datetime(rule.created_at),
        "updated_at": serialize_datetime(rule.updated_at),
    }


def serialize_alert_event(event: MonitoringAlertEvent, rule_name: str | None = None) -> dict[str, Any]:
    return {
        "id": event.id,
        "rule_id": event.rule_id,
        "rule_name": rule_name,
        "metric_value": event.metric_value,
        "status": event.status,
        "triggered_at": serialize_datetime(event.triggered_at),
        "resolved_at": serialize_datetime(event.resolved_at),
        "payload": parse_json_field(event.payload_json, {}),
    }


def compute_metric_value(logs: list[RequestLog], metric_key: str) -> tuple[float, int]:
    sample_count = len(logs)
    if sample_count == 0:
        return 0.0, 0

    if metric_key == "accuracy_drop":
        values = [1.0 if item.accuracy_hit else 0.0 for item in logs if item.accuracy_hit is not None]
        return (round(sum(values) / len(values), 4) if values else 0.0), sample_count
    if metric_key == "latency_p99_ms":
        return float(percentile([item.latency_ms for item in logs], 0.99)), sample_count
    if metric_key == "error_rate_spike":
        return round(sum(1 for item in logs if item.is_error) / sample_count, 4), sample_count
    return 0.0, sample_count


def compare_metric(metric_value: float, comparator: str, threshold: float) -> bool:
    if comparator == "gt":
        return metric_value > threshold
    if comparator == "gte":
        return metric_value >= threshold
    if comparator == "lt":
        return metric_value < threshold
    if comparator == "lte":
        return metric_value <= threshold
    return False


def evaluate_alert_rules(session: Session):
    now = datetime.utcnow()
    rules = session.execute(select(MonitoringAlertRule).order_by(MonitoringAlertRule.created_at.asc())).scalars().all()
    for rule in rules:
        cutoff = now - timedelta(minutes=rule.window_minutes)
        logs = session.execute(select(RequestLog).where(RequestLog.created_at >= cutoff)).scalars().all()
        metric_value, sample_count = compute_metric_value(logs, rule.metric_key)
        triggered = rule.enabled and compare_metric(metric_value, rule.comparator, rule.threshold)
        latest_unresolved = session.execute(
            select(MonitoringAlertEvent)
            .where(
                MonitoringAlertEvent.rule_id == rule.id,
                MonitoringAlertEvent.resolved_at.is_(None),
            )
            .order_by(MonitoringAlertEvent.triggered_at.desc())
        ).scalar_one_or_none()

        if triggered:
            if latest_unresolved is None:
                session.add(
                    MonitoringAlertEvent(
                        id=uuid.uuid4().hex,
                        rule_id=rule.id,
                        metric_value=metric_value,
                        status="open",
                        triggered_at=now,
                        payload_json=json.dumps({"window_minutes": rule.window_minutes, "samples": sample_count}),
                    )
                )
        elif latest_unresolved is not None:
            latest_unresolved.status = "resolved"
            latest_unresolved.resolved_at = now
            latest_unresolved.payload_json = json.dumps(
                {
                    **parse_json_field(latest_unresolved.payload_json, {}),
                    "resolved_metric_value": metric_value,
                    "samples": sample_count,
                }
            )
    session.commit()


@router.get("/monitoring/overview")
def get_monitoring_overview(
    request: Request,
    window: str = "15m",
    _: UserAccount = Depends(require_capability("monitoring_read")),
    session: Session = Depends(get_db),
):
    window_minutes = ensure_window_valid(window)
    evaluate_alert_rules(session)
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    logs = session.execute(select(RequestLog).where(RequestLog.created_at >= cutoff).order_by(RequestLog.created_at.desc())).scalars().all()
    rules = {item.id: item for item in session.execute(select(MonitoringAlertRule)).scalars().all()}
    events = session.execute(select(MonitoringAlertEvent).order_by(MonitoringAlertEvent.triggered_at.desc())).scalars().all()
    latest_alerts = [serialize_alert_event(item, rules.get(item.rule_id).name if rules.get(item.rule_id) else None) for item in events[:5]]
    return response_envelope(request, build_overview_payload(logs, latest_alerts, window_minutes))


@router.get("/monitoring/request-logs")
def list_request_logs(
    request: Request,
    window: str = "15m",
    device_id: str | None = None,
    route: str | None = None,
    intent: str | None = None,
    latency_min_ms: int | None = None,
    latency_max_ms: int | None = None,
    is_error: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    _: UserAccount = Depends(require_capability("monitoring_read")),
    session: Session = Depends(get_db),
):
    if page < 1 or page_size < 1:
        raise ApiError(422, "MON-422-WINDOW", "时间窗口或分页参数不合法")
    if latency_min_ms is not None and latency_min_ms < 0:
        raise ApiError(422, "MON-422-WINDOW", "时间窗口或分页参数不合法")
    if latency_max_ms is not None and latency_max_ms < 0:
        raise ApiError(422, "MON-422-WINDOW", "时间窗口或分页参数不合法")
    if latency_min_ms is not None and latency_max_ms is not None and latency_min_ms > latency_max_ms:
        raise ApiError(422, "MON-422-WINDOW", "时间窗口或分页参数不合法")

    window_minutes = ensure_window_valid(window)
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    items = session.execute(select(RequestLog).order_by(RequestLog.created_at.desc())).scalars().all()
    items = [item for item in items if item.created_at >= cutoff]
    if device_id:
        items = [item for item in items if item.device_id == device_id]
    if route:
        items = [item for item in items if item.route_type == route]
    if intent:
        items = [item for item in items if item.intent_name == intent]
    if latency_min_ms is not None:
        items = [item for item in items if item.latency_ms >= latency_min_ms]
    if latency_max_ms is not None:
        items = [item for item in items if item.latency_ms <= latency_max_ms]
    if is_error is not None:
        items = [item for item in items if item.is_error is is_error]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]
    return response_envelope(
        request,
        {
            "items": [serialize_request_log(item) for item in paged],
            "pagination": {"page": page, "page_size": page_size, "total": total},
        },
    )


@router.get("/monitoring/device-sessions")
def list_device_sessions(
    request: Request,
    device_id: str,
    _: UserAccount = Depends(require_capability("monitoring_read")),
    session: Session = Depends(get_db),
):
    logs = session.execute(
        select(RequestLog).where(RequestLog.device_id == device_id).order_by(RequestLog.created_at.asc())
    ).scalars().all()
    grouped: dict[str, list[RequestLog]] = {}
    for item in logs:
        grouped.setdefault(item.session_id, []).append(item)

    items = []
    for session_id, rounds in grouped.items():
        items.append(
            {
                "session_id": session_id,
                "device_id": device_id,
                "turn_count": len(rounds),
                "started_at": serialize_datetime(rounds[0].created_at),
                "ended_at": serialize_datetime(rounds[-1].created_at),
                "version": parse_json_field(rounds[-1].request_json, {}).get("version"),
            }
        )
    items.sort(key=lambda item: item["started_at"] or "", reverse=True)
    return response_envelope(request, {"items": items})


@router.get("/monitoring/sessions/{session_id}")
def get_session_trace(
    session_id: str,
    request: Request,
    _: UserAccount = Depends(require_capability("monitoring_read")),
    session: Session = Depends(get_db),
):
    logs = session.execute(
        select(RequestLog).where(RequestLog.session_id == session_id).order_by(RequestLog.created_at.asc())
    ).scalars().all()
    if not logs:
        raise ApiError(404, "MON-404-SESSION", "目标会话不存在或已过期")

    rounds = []
    for index, item in enumerate(logs, start=1):
        request_payload = parse_json_field(item.request_json, {})
        trace_payload = parse_json_field(item.response_json, {})
        rounds.append(
            {
                "round_no": index,
                "request_id": item.request_id,
                "input_text": request_payload.get("text"),
                "latency_ms": item.latency_ms,
                "is_error": item.is_error,
                "created_at": serialize_datetime(item.created_at),
                "trace": trace_payload,
            }
        )

    return response_envelope(
        request,
        {
            "session": {
                "session_id": session_id,
                "device_id": logs[0].device_id,
                "turn_count": len(logs),
                "started_at": serialize_datetime(logs[0].created_at),
                "ended_at": serialize_datetime(logs[-1].created_at),
            },
            "rounds": rounds,
        },
    )


@router.get("/monitoring/alert-rules")
def list_alert_rules(
    request: Request,
    _: UserAccount = Depends(require_capability("monitoring_read")),
    session: Session = Depends(get_db),
):
    evaluate_alert_rules(session)
    rules = session.execute(select(MonitoringAlertRule).order_by(MonitoringAlertRule.created_at.asc())).scalars().all()
    rule_map = {item.id: item for item in rules}
    events = session.execute(select(MonitoringAlertEvent).order_by(MonitoringAlertEvent.triggered_at.desc())).scalars().all()
    return response_envelope(
        request,
        {
            "rules": [serialize_alert_rule(item) for item in rules],
            "latest_events": [serialize_alert_event(item, rule_map.get(item.rule_id).name if rule_map.get(item.rule_id) else None) for item in events[:10]],
        },
    )


@router.post("/monitoring/alert-rules")
def create_alert_rule(
    payload: CreateAlertRulePayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("alert_manage")),
    session: Session = Depends(get_db),
):
    ensure_metric_valid(payload.metric_key)
    ensure_rule_fields_valid(payload.comparator, payload.severity, payload.threshold)
    existing = session.execute(select(MonitoringAlertRule).where(MonitoringAlertRule.name == payload.name.strip())).scalar_one_or_none()
    if existing is not None:
        raise ApiError(409, "MON-409-RULE-NAME", "告警规则名称已存在")

    rule = MonitoringAlertRule(
        id=uuid.uuid4().hex,
        name=payload.name.strip(),
        metric_key=payload.metric_key,
        comparator=payload.comparator,
        threshold=payload.threshold,
        window_minutes=payload.window_minutes,
        severity=payload.severity,
        enabled=True,
        created_by=actor.id,
    )
    session.add(rule)
    create_audit_log(session, actor.id, actor.id, "monitoring.alert_rule.create", {"rule_id": rule.id})
    session.commit()
    session.refresh(rule)
    return response_envelope(request, {"rule": serialize_alert_rule(rule)})


@router.patch("/monitoring/alert-rules/{rule_id}")
def update_alert_rule(
    rule_id: str,
    payload: UpdateAlertRulePayload,
    request: Request,
    actor: UserAccount = Depends(require_capability("alert_manage")),
    session: Session = Depends(get_db),
):
    rule = get_rule_or_404(session, rule_id)
    if payload.enabled is not None:
        rule.enabled = payload.enabled
    if payload.threshold is not None:
        if payload.threshold < 0:
            raise ApiError(422, "MON-422-THRESHOLD", "请检查阈值和比较器")
        rule.threshold = payload.threshold
    if payload.window_minutes is not None:
        rule.window_minutes = payload.window_minutes
    if payload.severity is not None:
        if payload.severity not in ALLOWED_SEVERITIES:
            raise ApiError(422, "MON-422-THRESHOLD", "请检查阈值和比较器")
        rule.severity = payload.severity

    create_audit_log(session, actor.id, actor.id, "monitoring.alert_rule.update", {"rule_id": rule.id})
    session.commit()
    session.refresh(rule)
    return response_envelope(request, {"rule": serialize_alert_rule(rule)})
