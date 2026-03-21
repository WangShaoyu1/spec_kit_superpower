"""Alert rule CRUD service."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.alert_event import AlertEvent
from app.models.alert_rule import AlertRule

logger = logging.getLogger(__name__)


def _serialize_rule(rule: AlertRule, last_fired_at=None) -> dict:
    return {
        "id": str(rule.id),
        "name": rule.name,
        "metric": rule.metric,
        "operator": rule.operator,
        "threshold": rule.threshold,
        "window_minutes": rule.window_minutes,
        "is_enabled": rule.is_enabled,
        "notification_channels": rule.notification_channels or [],
        "description": rule.description,
        "created_by": str(rule.created_by) if rule.created_by else None,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        "last_fired_at": last_fired_at.isoformat() if last_fired_at else None,
    }


def _serialize_event(event: AlertEvent, rule_name: str | None = None) -> dict:
    return {
        "id": str(event.id),
        "rule_id": str(event.rule_id),
        "rule_name": rule_name,
        "status": event.status,
        "metric_value": event.metric_value,
        "threshold_value": event.threshold_value,
        "fired_at": event.fired_at.isoformat() if event.fired_at else None,
        "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
        "message": event.message,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


async def list_rules(db: AsyncSession, page: int = 1, page_size: int = 20) -> dict:
    count_res = await db.execute(select(func.count(AlertRule.id)))
    total = count_res.scalar() or 0

    offset = (page - 1) * page_size
    last_fire = (
        select(
            AlertEvent.rule_id.label("rule_id"),
            func.max(AlertEvent.fired_at).label("last_fired_at"),
        )
        .group_by(AlertEvent.rule_id)
        .subquery()
    )
    result = await db.execute(
        select(AlertRule, last_fire.c.last_fired_at)
        .outerjoin(last_fire, AlertRule.id == last_fire.c.rule_id)
        .order_by(AlertRule.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    items = []
    for row in result.all():
        rule = row[0]
        lf = row[1]
        items.append(_serialize_rule(rule, lf))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_rule(db: AsyncSession, rule_id: UUID) -> dict:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise BusinessException("E50001", "告警规则不存在", http_status=404)
    return _serialize_rule(rule, None)


async def create_rule(db: AsyncSession, data: dict, user_id: str | None = None) -> dict:
    rule = AlertRule(**data)
    if user_id:
        rule.created_by = UUID(user_id)
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return _serialize_rule(rule, None)


async def update_rule(db: AsyncSession, rule_id: UUID, data: dict) -> dict:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise BusinessException("E50001", "告警规则不存在", http_status=404)

    for key, value in data.items():
        if value is not None:
            setattr(rule, key, value)

    await db.flush()
    await db.refresh(rule)
    return _serialize_rule(rule, None)


async def delete_rule(db: AsyncSession, rule_id: UUID) -> None:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise BusinessException("E50001", "告警规则不存在", http_status=404)
    await db.delete(rule)


async def toggle_rule(db: AsyncSession, rule_id: UUID, is_enabled: bool) -> dict:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise BusinessException("E50001", "告警规则不存在", http_status=404)
    rule.is_enabled = is_enabled
    await db.flush()
    await db.refresh(rule)
    return _serialize_rule(rule, None)


async def list_events(
    db: AsyncSession,
    *,
    rule_id: UUID | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    base = select(AlertEvent, AlertRule.name.label("rule_name")).join(
        AlertRule, AlertEvent.rule_id == AlertRule.id
    )
    count_q = select(func.count(AlertEvent.id))

    filters = []
    if rule_id:
        filters.append(AlertEvent.rule_id == rule_id)
    if status:
        filters.append(AlertEvent.status == status)

    for f in filters:
        base = base.where(f)
        count_q = count_q.where(f)

    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(AlertEvent.fired_at.desc()).offset(offset).limit(page_size)
    )

    items = []
    for row in result.all():
        event = row[0] if isinstance(row, tuple) else row.AlertEvent
        rule_name = row[1] if isinstance(row, tuple) else row.rule_name
        items.append(_serialize_event(event, rule_name=rule_name))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
