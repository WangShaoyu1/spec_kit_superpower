from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission
from app.models.request_log import RequestLog
from app.models.alert_rule import AlertRule

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/stats")
async def get_stats(
    hours: int = Query(default=24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.dashboard")),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    total = await db.execute(select(func.count(RequestLog.id)).where(RequestLog.created_at >= since))
    total_count = total.scalar() or 0

    avg_latency = await db.execute(
        select(func.avg(RequestLog.latency_ms)).where(RequestLog.created_at >= since)
    )
    avg_lat = avg_latency.scalar() or 0

    domain_counts = await db.execute(
        select(RequestLog.domain, func.count(RequestLog.id))
        .where(RequestLog.created_at >= since)
        .group_by(RequestLog.domain)
    )
    domains = {r[0]: r[1] for r in domain_counts.fetchall()}

    device_counts = await db.execute(
        select(func.count(func.distinct(RequestLog.device_id)))
        .where(RequestLog.created_at >= since)
    )
    unique_devices = device_counts.scalar() or 0

    return {
        "total_requests": total_count,
        "avg_latency_ms": round(float(avg_lat), 2),
        "domain_distribution": domains,
        "unique_devices": unique_devices,
        "time_range_hours": hours,
    }


@router.get("/devices/{device_id}/history")
async def get_device_history(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.dashboard")),
):
    result = await db.execute(
        select(RequestLog)
        .where(RequestLog.device_id == device_id)
        .order_by(RequestLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id), "input_text": l.input_text,
            "domain": l.domain, "intent": l.intent,
            "response_text": l.response_text,
            "latency_ms": l.latency_ms, "language": l.language,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.get("/logs")
async def list_logs(
    device_id: str | None = None,
    domain: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.dashboard")),
):
    query = select(RequestLog).order_by(RequestLog.created_at.desc()).limit(limit)
    if device_id:
        query = query.where(RequestLog.device_id == device_id)
    if domain:
        query = query.where(RequestLog.domain == domain)

    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id), "device_id": l.device_id,
            "input_text": l.input_text, "domain": l.domain,
            "intent": l.intent, "latency_ms": l.latency_ms,
            "language": l.language, "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


# ========== Alert Rules ==========

@router.post("/alerts", status_code=201)
async def create_alert_rule(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("monitoring.alerts")),
):
    rule = AlertRule(
        name=body["name"],
        metric_name=body["metric_name"],
        operator=body.get("operator", "lt"),
        threshold=body["threshold"],
        duration_minutes=body.get("duration_minutes", 5),
        notification_config=body.get("notification_config", {}),
        is_enabled=body.get("is_enabled", True),
        created_by=current_user.id,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {
        "id": str(rule.id), "name": rule.name,
        "metric_name": rule.metric_name, "operator": rule.operator,
        "threshold": float(rule.threshold),
        "duration_minutes": rule.duration_minutes,
        "is_enabled": rule.is_enabled,
        "created_at": rule.created_at.isoformat(),
    }


@router.get("/alerts")
async def list_alert_rules(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.alerts")),
):
    result = await db.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
    rules = result.scalars().all()
    return [
        {
            "id": str(r.id), "name": r.name,
            "metric_name": r.metric_name, "operator": r.operator,
            "threshold": float(r.threshold),
            "duration_minutes": r.duration_minutes,
            "is_enabled": r.is_enabled,
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ]


@router.patch("/alerts/{rule_id}")
async def update_alert_rule(
    rule_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.alerts")),
):
    rule = await db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    for field in ("name", "metric_name", "operator", "threshold", "duration_minutes", "is_enabled", "notification_config"):
        if field in body:
            setattr(rule, field, body[field])
    await db.commit()
    await db.refresh(rule)
    return {"id": str(rule.id), "name": rule.name, "is_enabled": rule.is_enabled}


@router.delete("/alerts/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.alerts")),
):
    rule = await db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    await db.delete(rule)
    await db.commit()
