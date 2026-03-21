"""Dashboard metrics aggregation with Redis caching."""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_event import AlertEvent
from app.models.request_log import RequestLog
from app.schemas.monitoring import DashboardMetrics, DomainDistribution, PreviousPeriodMetrics, TrendPoint

logger = logging.getLogger(__name__)

CACHE_PREFIX = "metrics:dashboard"
CACHE_TTL = 30  # seconds

TIME_RANGE_MAP = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _resolve_windows(
    time_range: str | None,
    range_start: datetime | None,
    range_end: datetime | None,
) -> tuple[datetime, datetime, datetime, datetime]:
    """Return current_start, current_end, prev_start, prev_end (all UTC-aware)."""
    now = datetime.now(timezone.utc)
    if range_start is not None and range_end is not None:
        current_start = range_start if range_start.tzinfo else range_start.replace(tzinfo=timezone.utc)
        current_end = range_end if range_end.tzinfo else range_end.replace(tzinfo=timezone.utc)
        if current_end > now:
            current_end = now
        if current_start > current_end:
            current_start = current_end - timedelta(hours=1)
    else:
        delta = TIME_RANGE_MAP.get(time_range or "24h", timedelta(hours=24))
        current_end = now
        current_start = current_end - delta

    duration = current_end - current_start
    prev_end = current_start
    prev_start = current_start - duration
    return current_start, current_end, prev_start, prev_end


async def _aggregate_period(
    db: AsyncSession,
    start: datetime,
    end: datetime,
) -> dict:
    """Aggregate request log metrics for [start, end] (inclusive-ish upper bound)."""
    agg = await db.execute(
        select(
            func.count(RequestLog.id).label("total"),
            func.sum(case((RequestLog.status == "success", 1), else_=0)).label("success_count"),
            func.coalesce(func.avg(RequestLog.latency_ms), 0).label("avg_lat"),
            func.coalesce(func.avg(RequestLog.confidence), 0).label("avg_conf"),
        )
        .select_from(RequestLog)
        .where(RequestLog.created_at >= start, RequestLog.created_at <= end)
    )
    row = agg.first()
    total = int(row.total) if row and row.total else 0
    success_count = int(row.success_count) if row and row.success_count else 0
    avg_lat = float(row.avg_lat) if row and row.avg_lat is not None else 0.0
    avg_conf = float(row.avg_conf) if row and row.avg_conf is not None else 0.0

    try:
        p99_res = await db.execute(
            text(
                "SELECT COALESCE(percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms), 0) "
                "FROM request_logs WHERE created_at >= :start AND created_at <= :end "
                "AND latency_ms IS NOT NULL"
            ),
            {"start": start, "end": end},
        )
        p99 = float(p99_res.scalar() or 0)
    except Exception:
        p99 = 0.0

    success_rate = (success_count / total * 100) if total > 0 else 0.0
    intent_accuracy = round(avg_conf * 100, 1) if avg_conf else 0.0

    sess_res = await db.execute(
        select(func.count(func.distinct(RequestLog.session_id)))
        .select_from(RequestLog)
        .where(
            RequestLog.created_at >= start,
            RequestLog.created_at <= end,
            RequestLog.session_id.isnot(None),
        )
    )
    dialog_turns = int(sess_res.scalar() or 0)

    domain_rows = await db.execute(
        select(RequestLog.domain, func.count(RequestLog.id).label("cnt"))
        .select_from(RequestLog)
        .where(
            RequestLog.created_at >= start,
            RequestLog.created_at <= end,
            RequestLog.domain.isnot(None),
        )
        .group_by(RequestLog.domain)
        .order_by(func.count(RequestLog.id).desc())
    )
    domains = []
    for d_row in domain_rows.all():
        pct = (d_row.cnt / total * 100) if total > 0 else 0.0
        domains.append(
            DomainDistribution(domain=d_row.domain, count=d_row.cnt, percentage=round(pct, 1))
        )

    secs = max((end - start).total_seconds(), 1.0)
    qps = round(total / secs, 2)

    return {
        "request_count": total,
        "success_rate": round(success_rate, 2),
        "avg_latency": round(avg_lat, 1),
        "p99_latency": round(p99, 1),
        "domain_distribution": domains,
        "qps": qps,
        "intent_accuracy": intent_accuracy,
        "dialog_turns": dialog_turns,
    }


async def get_dashboard_metrics(
    db: AsyncSession,
    redis,
    time_range: str | None = "24h",
    range_start: datetime | None = None,
    range_end: datetime | None = None,
) -> DashboardMetrics:
    use_custom = range_start is not None and range_end is not None
    cache_key = f"{CACHE_PREFIX}:{time_range}" if not use_custom and time_range else None

    if cache_key and redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return DashboardMetrics(**json.loads(cached))
        except Exception:
            logger.debug("Redis cache miss for %s", cache_key)

    c_start, c_end, p_start, p_end = _resolve_windows(time_range, range_start, range_end)

    current = await _aggregate_period(db, c_start, c_end)
    previous = await _aggregate_period(db, p_start, p_end)

    alert_count_res = await db.execute(
        select(func.count(AlertEvent.id))
        .select_from(AlertEvent)
        .where(AlertEvent.status == "firing")
    )
    active_alerts = int(alert_count_res.scalar() or 0)

    prev_model = PreviousPeriodMetrics(
        request_count=previous["request_count"],
        success_rate=previous["success_rate"],
        avg_latency=previous["avg_latency"],
        p99_latency=previous["p99_latency"],
        domain_distribution=previous["domain_distribution"],
        qps=previous["qps"],
        intent_accuracy=previous["intent_accuracy"],
        dialog_turns=previous["dialog_turns"],
    )

    metrics = DashboardMetrics(
        request_count=current["request_count"],
        success_rate=current["success_rate"],
        avg_latency=current["avg_latency"],
        p99_latency=current["p99_latency"],
        active_alerts=active_alerts,
        domain_distribution=current["domain_distribution"],
        qps=current["qps"],
        intent_accuracy=current["intent_accuracy"],
        dialog_turns=current["dialog_turns"],
        previous_period=prev_model,
    )

    if cache_key and redis:
        try:
            await redis.set(cache_key, metrics.model_dump_json(), ex=CACHE_TTL)
        except Exception:
            pass

    return metrics


async def get_trend_data(
    db: AsyncSession,
    time_range: str | None = "24h",
    interval: str = "1h",
    range_start: datetime | None = None,
    range_end: datetime | None = None,
) -> list[TrendPoint]:
    now = datetime.now(timezone.utc)
    if range_start is not None and range_end is not None:
        since = range_start if range_start.tzinfo else range_start.replace(tzinfo=timezone.utc)
        until = range_end if range_end.tzinfo else range_end.replace(tzinfo=timezone.utc)
        if until > now:
            until = now
    else:
        delta = TIME_RANGE_MAP.get(time_range or "24h", timedelta(hours=24))
        until = now
        since = until - delta

    interval_map = {
        "5m": "5 minutes",
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day",
    }
    pg_interval = interval_map.get(interval, "1 hour")

    result = await db.execute(
        text(
            f"""
            SELECT
                date_trunc('hour', created_at) +
                    (EXTRACT(EPOCH FROM created_at - date_trunc('hour', created_at))::int
                     / EXTRACT(EPOCH FROM interval '{pg_interval}')::int)
                    * interval '{pg_interval}' AS time_bucket,
                COUNT(*) AS request_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
                COALESCE(AVG(latency_ms), 0) AS avg_latency
            FROM request_logs
            WHERE created_at >= :since AND created_at <= :until
            GROUP BY time_bucket
            ORDER BY time_bucket
            """
        ),
        {"since": since, "until": until},
    )

    return [
        TrendPoint(
            time_bucket=row.time_bucket.isoformat() if row.time_bucket else "",
            request_count=row.request_count,
            error_count=row.error_count,
            avg_latency=round(float(row.avg_latency), 1),
        )
        for row in result.all()
    ]
