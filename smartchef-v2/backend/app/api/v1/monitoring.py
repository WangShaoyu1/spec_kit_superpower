"""Monitoring API routes — dashboard, device logs, alert rules, alert events."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import paginated_response, success_response
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import require_capability
from app.schemas.monitoring import (
    CreateAlertRuleRequest,
    ToggleAlertRuleRequest,
    UpdateAlertRuleRequest,
)
from app.services.monitoring import alert_service, log_service, metrics_service

router = APIRouter(tags=["monitoring"])


# ── Dashboard ──────────────────────────────────────────────────────────────


@router.get("/monitoring/dashboard")
@require_capability("monitoring_read")
async def dashboard_metrics(
    request: Request,
    time_range: str = Query("24h", pattern=r"^(1h|6h|24h|7d|30d)$"),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()
    rs = start_time if start_time and end_time else None
    re = end_time if start_time and end_time else None
    data = await metrics_service.get_dashboard_metrics(
        db, redis, time_range=time_range, range_start=rs, range_end=re
    )
    return success_response(data.model_dump())


@router.get("/monitoring/dashboard/trend")
@require_capability("monitoring_read")
async def dashboard_trend(
    request: Request,
    time_range: str = Query("24h", pattern=r"^(1h|6h|24h|7d|30d)$"),
    interval: str = Query("1h", pattern=r"^(5m|15m|1h|6h|1d)$"),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    rs = start_time if start_time and end_time else None
    re = end_time if start_time and end_time else None
    data = await metrics_service.get_trend_data(
        db, time_range, interval, range_start=rs, range_end=re
    )
    return success_response([p.model_dump() for p in data])


# ── Device Logs ────────────────────────────────────────────────────────────


@router.get("/monitoring/logs")
@require_capability("monitoring_read")
async def query_logs(
    request: Request,
    device_id: str | None = Query(None),
    session_id: str | None = Query(None),
    domain: str | None = Query(None, pattern=r"^(command|knowledge|chitchat)$"),
    intent: str | None = Query(None),
    status: str | None = Query(None, pattern=r"^(success|error)$"),
    latency_min: int | None = Query(None, ge=0),
    latency_max: int | None = Query(None, ge=0),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await log_service.query_logs(
        db,
        device_id=device_id,
        session_id=session_id,
        domain=domain,
        intent=intent,
        status=status,
        latency_min=latency_min,
        latency_max=latency_max,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data["items"], total=data["total"], page=data["page"], page_size=data["page_size"]
    )


@router.get("/monitoring/sessions/{session_id}/traces")
@require_capability("monitoring_read")
async def session_trace(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    data = await log_service.get_session_trace(db, session_id)
    return success_response(data)


@router.get("/monitoring/devices/{device_id}/sessions")
@require_capability("monitoring_read")
async def device_sessions(
    request: Request,
    device_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await log_service.get_device_sessions(db, device_id, page=page, page_size=page_size)
    return paginated_response(
        data["items"], total=data["total"], page=data["page"], page_size=data["page_size"]
    )


# ── Alert Rules ────────────────────────────────────────────────────────────


@router.get("/alert-rules")
@require_capability("monitoring_manage")
async def list_alert_rules(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await alert_service.list_rules(db, page=page, page_size=page_size)
    return paginated_response(
        data["items"], total=data["total"], page=data["page"], page_size=data["page_size"]
    )


@router.post("/alert-rules")
@require_capability("monitoring_manage")
async def create_alert_rule(
    request: Request,
    body: CreateAlertRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "current_user", None)
    uid = user_id.user_id if user_id else None
    data = await alert_service.create_rule(db, body.model_dump(), user_id=uid)
    return success_response(data, status_code=201)


@router.get("/alert-rules/{rule_id}")
@require_capability("monitoring_manage")
async def get_alert_rule(
    request: Request,
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await alert_service.get_rule(db, rule_id)
    return success_response(data)


@router.put("/alert-rules/{rule_id}")
@require_capability("monitoring_manage")
async def update_alert_rule(
    request: Request,
    rule_id: UUID,
    body: UpdateAlertRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await alert_service.update_rule(db, rule_id, body.model_dump(exclude_unset=True))
    return success_response(data)


@router.delete("/alert-rules/{rule_id}")
@require_capability("monitoring_manage")
async def delete_alert_rule(
    request: Request,
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await alert_service.delete_rule(db, rule_id)
    return success_response(None, msg="告警规则已删除")


@router.put("/alert-rules/{rule_id}/toggle")
@require_capability("monitoring_manage")
async def toggle_alert_rule(
    request: Request,
    rule_id: UUID,
    body: ToggleAlertRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await alert_service.toggle_rule(db, rule_id, body.is_enabled)
    return success_response(data)


# ── Alert Events ───────────────────────────────────────────────────────────


@router.get("/alert-events")
@require_capability("monitoring_manage")
async def list_alert_events(
    request: Request,
    rule_id: UUID | None = Query(None),
    status: str | None = Query(None, pattern=r"^(pending|firing|resolved)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await alert_service.list_events(
        db, rule_id=rule_id, status=status, page=page, page_size=page_size
    )
    return paginated_response(
        data["items"], total=data["total"], page=data["page"], page_size=data["page_size"]
    )
