"""Log query service for monitoring device logs and session traces."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)


def _serialize_log(row: RequestLog) -> dict:
    return {
        "id": str(row.id),
        "request_id": row.request_id,
        "session_id": row.session_id,
        "device_id": row.device_id,
        "input_text": row.input_text,
        "domain": row.domain,
        "intent": row.intent,
        "slots": row.slots or {},
        "confidence": row.confidence,
        "latency_ms": row.latency_ms,
        "status": row.status,
        "error_message": row.error_message,
        "response_text": row.response_text,
        "model_version": row.model_version,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


async def query_logs(
    db: AsyncSession,
    *,
    device_id: str | None = None,
    session_id: str | None = None,
    domain: str | None = None,
    intent: str | None = None,
    status: str | None = None,
    latency_min: int | None = None,
    latency_max: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    base = select(RequestLog)
    count_q = select(func.count(RequestLog.id))

    filters = []
    if device_id:
        filters.append(RequestLog.device_id == device_id)
    if session_id:
        filters.append(RequestLog.session_id == session_id)
    if domain:
        filters.append(RequestLog.domain == domain)
    if intent:
        filters.append(RequestLog.intent.ilike(f"%{intent}%"))
    if status:
        filters.append(RequestLog.status == status)
    if latency_min is not None:
        filters.append(RequestLog.latency_ms >= latency_min)
    if latency_max is not None:
        filters.append(RequestLog.latency_ms <= latency_max)
    if start_time:
        filters.append(RequestLog.created_at >= start_time)
    if end_time:
        filters.append(RequestLog.created_at <= end_time)

    for f in filters:
        base = base.where(f)
        count_q = count_q.where(f)

    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    offset = (page - 1) * page_size
    query = base.order_by(RequestLog.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "items": [_serialize_log(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_session_trace(db: AsyncSession, session_id: str) -> dict:
    query = (
        select(RequestLog)
        .where(RequestLog.session_id == session_id)
        .order_by(RequestLog.created_at.asc())
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    messages = [_serialize_log(r) for r in rows]
    device_id = rows[0].device_id if rows else None
    start_time = rows[0].created_at.isoformat() if rows else None
    end_time = rows[-1].created_at.isoformat() if rows else None

    return {
        "session_id": session_id,
        "device_id": device_id,
        "messages": messages,
        "total_messages": len(messages),
        "start_time": start_time,
        "end_time": end_time,
    }


async def get_device_sessions(
    db: AsyncSession,
    device_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    count_q = (
        select(func.count(func.distinct(RequestLog.session_id)))
        .where(RequestLog.device_id == device_id, RequestLog.session_id.isnot(None))
    )
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(
            RequestLog.session_id,
            func.count(RequestLog.id).label("message_count"),
            func.min(RequestLog.created_at).label("first_message_at"),
            func.max(RequestLog.created_at).label("last_message_at"),
            func.array_agg(func.distinct(RequestLog.domain)).label("domains"),
        )
        .where(RequestLog.device_id == device_id, RequestLog.session_id.isnot(None))
        .group_by(RequestLog.session_id)
        .order_by(func.max(RequestLog.created_at).desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)

    items = []
    for row in result.all():
        domains = [d for d in (row.domains or []) if d is not None]
        items.append({
            "session_id": row.session_id,
            "message_count": row.message_count,
            "first_message_at": row.first_message_at.isoformat() if row.first_message_at else None,
            "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
            "domains": domains,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
