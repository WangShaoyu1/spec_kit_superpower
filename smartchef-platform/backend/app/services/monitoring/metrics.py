"""指标聚合服务：QPS、延迟、准确率、路由分布、错误率等。"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog


async def get_dashboard_metrics(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    hours: int = 24,
) -> dict:
    """
    聚合查询仪表盘核心指标（FR-030）。

    返回：
    - total_requests: 总请求量
    - qps: 每秒请求数（按时间范围平均）
    - avg_latency_ms: 平均延迟
    - p95_latency_ms: P95 延迟
    - p99_latency_ms: P99 延迟
    - intent_accuracy: 意图准确率（以 command 域平均置信度近似）
    - route_distribution: 路由分布（command/knowledge/chitchat 占比）
    - error_rate: 错误率
    - unique_devices: 独立设备数
    """
    now = datetime.now(timezone.utc)
    start = since or (now - timedelta(hours=hours))
    delta = now - start
    seconds = max(1, delta.total_seconds())

    base = RequestLog.created_at >= start

    # 总请求量
    total_row = await db.execute(
        select(func.count(RequestLog.id)).where(base)
    )
    total = total_row.scalar() or 0

    # 平均延迟
    avg_row = await db.execute(
        select(func.avg(RequestLog.latency_ms)).where(base)
    )
    avg_lat = avg_row.scalar() or 0
    avg_latency = round(float(avg_lat), 2) if avg_lat else 0

    # P95 / P99（PostgreSQL percentile_cont）
    p95_row = await db.execute(
        select(func.percentile_cont(0.95).within_group(RequestLog.latency_ms))
        .where(base)
    )
    p95_val = p95_row.scalar()
    p95_latency = int(p95_val) if p95_val is not None else 0

    p99_row = await db.execute(
        select(func.percentile_cont(0.99).within_group(RequestLog.latency_ms))
        .where(base)
    )
    p99_val = p99_row.scalar()
    p99_latency = int(p99_val) if p99_val is not None else 0

    # 意图准确率：command 域下平均 intent_confidence 作为近似
    cmd_avg = await db.execute(
        select(func.avg(RequestLog.intent_confidence))
        .where(base, RequestLog.domain == "command")
    )
    intent_acc = cmd_avg.scalar()
    intent_accuracy = round(float(intent_acc), 4) if intent_acc is not None else None

    # 路由分布
    route_rows = await db.execute(
        select(RequestLog.domain, func.count(RequestLog.id))
        .where(base)
        .group_by(RequestLog.domain)
    )
    route_counts = {r[0]: r[1] for r in route_rows.fetchall()}
    total_for_route = sum(route_counts.values()) or 1
    route_distribution = {
        k: round(v / total_for_route, 4)
        for k, v in route_counts.items()
    }

    # 错误率（从 extra.is_error 或 domain=error 推断）
    # 当前模型无 is_error 列，用 domain='error' 或 extra 中的 is_error
    err_row = await db.execute(
        select(func.count(RequestLog.id))
        .where(base, RequestLog.domain == "error")
    )
    err_count = err_row.scalar() or 0
    # 也可查询 extra->>'is_error' = 'true'，当前简化用 domain
    error_rate = round(err_count / max(1, total), 4)

    # 独立设备数
    dev_row = await db.execute(
        select(func.count(func.distinct(RequestLog.device_id))).where(base)
    )
    unique_devices = dev_row.scalar() or 0

    qps = round(total / seconds, 2) if seconds else 0

    return {
        "total_requests": total,
        "qps": qps,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "p99_latency_ms": p99_latency,
        "intent_accuracy": intent_accuracy,
        "route_distribution": route_distribution,
        "error_rate": error_rate,
        "unique_devices": unique_devices,
        "since": start.isoformat(),
        "hours": hours,
    }
