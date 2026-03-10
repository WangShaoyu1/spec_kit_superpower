"""日志查询服务：多维筛选、设备会话、会话详情。"""
from datetime import datetime, timezone

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog


async def query_logs(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    device_id: str | None = None,
    route_type: str | None = None,
    intent_name: str | None = None,
    latency_min_ms: int | None = None,
    latency_max_ms: int | None = None,
    is_error: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """
    多维筛选请求日志（FR-034）。

    支持：时间范围、设备 ID、路由类型、意图名称、耗时区间、是否异常。
    """
    conds = []
    if since:
        conds.append(RequestLog.created_at >= since)
    if until:
        conds.append(RequestLog.created_at <= until)
    if device_id:
        conds.append(RequestLog.device_id == device_id)
    if route_type:
        conds.append(RequestLog.domain == route_type)
    if intent_name:
        conds.append(RequestLog.intent == intent_name)
    if latency_min_ms is not None:
        conds.append(RequestLog.latency_ms >= latency_min_ms)
    if latency_max_ms is not None:
        conds.append(RequestLog.latency_ms <= latency_max_ms)
    if is_error is not None:
        if is_error:
            # domain=error 或 extra->>'is_error' = 'true'
            conds.append(
                (RequestLog.domain == "error")
                | (RequestLog.extra["is_error"].astext == "true")
            )
        else:
            # 排除异常：domain!=error 且 (extra 无 is_error 或 is_error 非 true)
            conds.append(
                (RequestLog.domain != "error")
                & or_(
                    RequestLog.extra.is_(None),
                    RequestLog.extra["is_error"].is_(None),
                    RequestLog.extra["is_error"].astext != "true",
                )
            )

    where = and_(*conds) if conds else True

    result = await db.execute(
        select(RequestLog)
        .where(where)
        .order_by(RequestLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()

    return [_log_to_dict(l) for l in logs]


def _log_to_dict(l: RequestLog) -> dict:
    """将 RequestLog 转为可序列化 dict。"""
    extra = l.extra or {}
    return {
        "id": str(l.id),
        "request_id": extra.get("request_id"),
        "device_id": l.device_id,
        "session_id": l.session_id,
        "input_text": l.input_text,
        "route_result": l.domain,
        "route_confidence": extra.get("route_confidence"),
        "intent": l.intent,
        "intent_confidence": l.intent_confidence,
        "slots_extracted": extra.get("slots_extracted"),
        "response_text": l.response_text,
        "knowledge_hit": extra.get("knowledge_hit"),
        "device_context": extra.get("device_context"),
        "latency_ms": l.latency_ms,
        "is_error": extra.get("is_error", l.domain == "error"),
        "error_detail": extra.get("error_detail"),
        "language": l.language,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }


async def get_device_sessions(
    db: AsyncSession,
    device_id: str,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    按设备 ID 获取历史会话列表（FR-031）。

    返回：会话ID、起止时间、轮数、使用版本（若记录）
    """
    conds = [RequestLog.device_id == device_id]
    if since:
        conds.append(RequestLog.created_at >= since)
    if until:
        conds.append(RequestLog.created_at <= until)

    # 按 session_id 聚合
    result = await db.execute(
        select(
            RequestLog.session_id,
            func.min(RequestLog.created_at).label("start_at"),
            func.max(RequestLog.created_at).label("end_at"),
            func.count(RequestLog.id).label("turn_count"),
        )
        .where(and_(*conds))
        .group_by(RequestLog.session_id)
        .order_by(func.max(RequestLog.created_at).desc())
        .limit(limit)
    )
    rows = result.fetchall()

    sessions = []
    for r in rows:
        sid = r.session_id or "(无会话)"
        sessions.append({
            "session_id": sid,
            "start_at": r.start_at.isoformat() if r.start_at else None,
            "end_at": r.end_at.isoformat() if r.end_at else None,
            "turn_count": r.turn_count,
        })
    return sessions


async def get_session_detail(
    db: AsyncSession,
    session_id: str,
    device_id: str | None = None,
) -> dict | None:
    """
    获取单个会话的每轮请求链路（FR-032）。

    返回：会话元信息 + 每轮完整链路（输入、路由、意图、槽位、响应、耗时、设备上下文等）
    """
    conds = [RequestLog.session_id == session_id]
    if device_id:
        conds.append(RequestLog.device_id == device_id)

    result = await db.execute(
        select(RequestLog)
        .where(and_(*conds))
        .order_by(RequestLog.created_at.asc())
    )
    logs = result.scalars().all()
    if not logs:
        return None

    turns = [_log_to_dict(l) for l in logs]
    first, last = logs[0], logs[-1]
    return {
        "session_id": session_id,
        "device_id": first.device_id,
        "start_at": first.created_at.isoformat() if first.created_at else None,
        "end_at": last.created_at.isoformat() if last.created_at else None,
        "turn_count": len(logs),
        "turns": turns,
    }
