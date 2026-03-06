from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission
from app.models.request_log import RequestLog

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/stats")
async def get_stats(
    hours: int = Query(default=24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("monitoring.read")),
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

    avg_turns = await db.execute(
        select(func.avg(
            select(func.count(RequestLog.id)).where(
                RequestLog.session_id == RequestLog.session_id
            ).correlate(RequestLog).scalar_subquery()
        )).where(RequestLog.created_at >= since)
    )

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
    _=Depends(require_permission("monitoring.read")),
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
    _=Depends(require_permission("monitoring.read")),
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
