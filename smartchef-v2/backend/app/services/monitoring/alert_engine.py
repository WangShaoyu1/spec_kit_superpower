"""Alert evaluation engine — checks rules against current metrics.

State machine: pending → firing → resolved
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_event import AlertEvent
from app.models.alert_rule import AlertRule
from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)

OPERATOR_MAP = {
    "gt": lambda v, t: v > t,
    "lt": lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
    "eq": lambda v, t: v == t,
}


async def _compute_metric(db: AsyncSession, metric: str, window_minutes: int) -> float:
    since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    if metric == "request_count":
        result = await db.execute(
            select(func.count(RequestLog.id)).where(RequestLog.created_at >= since)
        )
        return float(result.scalar() or 0)

    if metric == "error_rate":
        result = await db.execute(
            select(
                func.count(RequestLog.id).label("total"),
                func.sum(case((RequestLog.status == "error", 1), else_=0)).label("errors"),
            ).where(RequestLog.created_at >= since)
        )
        row = result.first()
        if not row or row.total == 0:
            return 0.0
        return float(row.errors) / float(row.total) * 100

    if metric == "avg_latency":
        result = await db.execute(
            select(func.coalesce(func.avg(RequestLog.latency_ms), 0)).where(
                RequestLog.created_at >= since, RequestLog.latency_ms.isnot(None)
            )
        )
        return float(result.scalar() or 0)

    if metric == "p99_latency":
        try:
            result = await db.execute(
                text(
                    "SELECT COALESCE(percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms), 0) "
                    "FROM request_logs WHERE created_at >= :since AND latency_ms IS NOT NULL"
                ),
                {"since": since},
            )
            return float(result.scalar() or 0)
        except Exception:
            return 0.0

    return 0.0


async def create_event(db: AsyncSession, rule: AlertRule, value: float) -> AlertEvent:
    event = AlertEvent(
        rule_id=rule.id,
        status="firing",
        metric_value=value,
        threshold_value=rule.threshold,
        message=f"[{rule.name}] {rule.metric} = {value:.2f} {rule.operator} {rule.threshold}",
    )
    db.add(event)
    await db.flush()
    return event


async def evaluate_rules(db: AsyncSession, redis=None) -> list[dict]:
    """Evaluate all enabled alert rules and create/resolve events."""
    result = await db.execute(
        select(AlertRule).where(AlertRule.is_enabled.is_(True))
    )
    rules = result.scalars().all()
    triggered = []

    for rule in rules:
        value = await _compute_metric(db, rule.metric, rule.window_minutes)
        comparator = OPERATOR_MAP.get(rule.operator)
        if not comparator:
            continue

        is_violated = comparator(value, rule.threshold)

        # Check existing firing events for this rule
        existing = await db.execute(
            select(AlertEvent)
            .where(AlertEvent.rule_id == rule.id, AlertEvent.status == "firing")
            .order_by(AlertEvent.fired_at.desc())
            .limit(1)
        )
        active_event = existing.scalar_one_or_none()

        if is_violated and not active_event:
            event = await create_event(db, rule, value)
            triggered.append({
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "metric_value": value,
                "threshold": rule.threshold,
                "event_id": str(event.id),
            })
            logger.warning("Alert fired: %s (value=%.2f, threshold=%.2f)", rule.name, value, rule.threshold)
        elif not is_violated and active_event:
            active_event.status = "resolved"
            active_event.resolved_at = datetime.now(timezone.utc)
            logger.info("Alert resolved: %s", rule.name)

    return triggered
