"""告警引擎：规则 CRUD、阈值检查与触发。"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog
from app.models.alert_rule import AlertRule
from app.services.monitoring.metrics import get_dashboard_metrics


# 支持的指标与运算符
VALID_METRICS = {"accuracy", "p95_latency", "p99_latency", "error_rate"}
VALID_OPERATORS = {"lt", "gt", "lte", "gte"}


def _evaluate(operator: str, value: float | None, threshold: Decimal) -> bool:
    """判断 value op threshold 是否成立。"""
    if value is None:
        return False
    t = float(threshold)
    if operator == "lt":
        return value < t
    if operator == "gt":
        return value > t
    if operator == "lte":
        return value <= t
    if operator == "gte":
        return value >= t
    return False


async def check_alerts(db: AsyncSession) -> list[dict]:
    """
    检查所有启用的告警规则是否触发（FR-035）。

    在指定 duration_minutes 时间窗口内，若指标持续满足阈值则触发。
    返回：触发的规则列表及当前指标值。
    """
    triggered = []
    result = await db.execute(
        select(AlertRule).where(AlertRule.is_enabled == True)
    )
    rules = result.scalars().all()

    for rule in rules:
        if rule.metric_name not in VALID_METRICS or rule.operator not in VALID_OPERATORS:
            continue

        # 取规则持续时间内的指标
        since = datetime.now(timezone.utc) - timedelta(minutes=rule.duration_minutes)
        metrics = await get_dashboard_metrics(db, since=since)

        value = None
        if rule.metric_name == "accuracy":
            value = metrics.get("intent_accuracy")
        elif rule.metric_name == "p95_latency":
            value = metrics.get("p95_latency_ms")
        elif rule.metric_name == "p99_latency":
            value = metrics.get("p99_latency_ms")
        elif rule.metric_name == "error_rate":
            value = metrics.get("error_rate")

        if _evaluate(rule.operator, value, rule.threshold):
            triggered.append({
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "metric_name": rule.metric_name,
                "operator": rule.operator,
                "threshold": float(rule.threshold),
                "actual_value": value,
                "duration_minutes": rule.duration_minutes,
                "notification_config": rule.notification_config,
            })
    return triggered


async def create_alert_rule(
    db: AsyncSession,
    *,
    name: str,
    metric_name: str,
    operator: str,
    threshold: float | Decimal,
    duration_minutes: int,
    notification_config: dict,
    is_enabled: bool = True,
    created_by: UUID | None = None,
) -> AlertRule:
    """
    创建告警规则。
    """
    if metric_name not in VALID_METRICS:
        raise ValueError(f"metric_name 必须是 {VALID_METRICS} 之一")
    if operator not in VALID_OPERATORS:
        raise ValueError(f"operator 必须是 {VALID_OPERATORS} 之一")

    rule = AlertRule(
        name=name,
        metric_name=metric_name,
        operator=operator,
        threshold=Decimal(str(threshold)),
        duration_minutes=duration_minutes,
        notification_config=notification_config,
        is_enabled=is_enabled,
        created_by=created_by,
    )
    db.add(rule)
    await db.flush()
    return rule


async def update_alert_rule(
    db: AsyncSession,
    rule_id: UUID,
    *,
    name: str | None = None,
    metric_name: str | None = None,
    operator: str | None = None,
    threshold: float | Decimal | None = None,
    duration_minutes: int | None = None,
    notification_config: dict | None = None,
    is_enabled: bool | None = None,
) -> AlertRule | None:
    """
    更新告警规则。未提供的字段保持不变。
    """
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return None

    if name is not None:
        rule.name = name
    if metric_name is not None:
        if metric_name not in VALID_METRICS:
            raise ValueError(f"metric_name 必须是 {VALID_METRICS} 之一")
        rule.metric_name = metric_name
    if operator is not None:
        if operator not in VALID_OPERATORS:
            raise ValueError(f"operator 必须是 {VALID_OPERATORS} 之一")
        rule.operator = operator
    if threshold is not None:
        rule.threshold = Decimal(str(threshold))
    if duration_minutes is not None:
        rule.duration_minutes = duration_minutes
    if notification_config is not None:
        rule.notification_config = notification_config
    if is_enabled is not None:
        rule.is_enabled = is_enabled

    await db.flush()
    return rule


async def get_alert_rule(db: AsyncSession, rule_id: UUID) -> AlertRule | None:
    """获取单条告警规则。"""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    return result.scalar_one_or_none()


async def list_alert_rules(
    db: AsyncSession,
    *,
    is_enabled: bool | None = None,
) -> list[AlertRule]:
    """列出告警规则。"""
    query = select(AlertRule)
    if is_enabled is not None:
        query = query.where(AlertRule.is_enabled == is_enabled)
    result = await db.execute(query.order_by(AlertRule.created_at.desc()))
    return list(result.scalars().all())


async def delete_alert_rule(db: AsyncSession, rule_id: UUID) -> bool:
    """删除告警规则。"""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return False
    await db.delete(rule)
    await db.flush()
    return True
