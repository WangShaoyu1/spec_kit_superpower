"""
T140 FR-037: GDPR 合规 — 按设备 ID 维度的数据导出和数据删除 API。
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import require_permission
from app.models.request_log import RequestLog
from app.services.session.device_session import get_session, delete_session

router = APIRouter(prefix="/data", tags=["数据管理 (GDPR)"])


def _row_to_dict(row: RequestLog) -> dict:
    """将 RequestLog 行转为可序列化字典。"""
    return {
        "id": str(row.id),
        "device_id": row.device_id,
        "session_id": row.session_id,
        "input_text": row.input_text,
        "domain": row.domain,
        "intent": row.intent,
        "response_text": row.response_text,
        "latency_ms": row.latency_ms,
        "intent_confidence": row.intent_confidence,
        "language": row.language,
        "extra": row.extra,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/export/{device_id}")
async def export_device_data(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(require_permission("data_management")),
):
    """
    导出指定设备的全部数据（JSON 格式），用于 GDPR 数据可携带权。

    包含：对话历史（RequestLog）、会话数据（Redis）。
    """
    # 查询该设备所有 RequestLog
    result = await db.execute(select(RequestLog).where(RequestLog.device_id == device_id).order_by(RequestLog.created_at))
    logs = result.scalars().all()

    # 获取 Redis 会话
    session_data = await get_session(redis, device_id)

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id,
        "request_logs": [_row_to_dict(r) for r in logs],
        "session": session_data,
    }
    return JSONResponse(content=payload)


@router.delete("/{device_id}")
async def delete_device_data(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    confirm: bool = Query(..., description="必须传 confirm=true 以确认删除（管理员二次确认）"),
    _=Depends(require_permission("data_management")),
):
    """
    删除指定设备的全部数据，用于 GDPR 被遗忘权。

    将删除：RequestLog 中该设备的记录、Redis 中该设备的会话。
    删除操作需管理员二次确认（传 confirm=true）。
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="删除操作需传 confirm=true 进行二次确认")

    # 删除 RequestLog（批量删除）
    result = await db.execute(delete(RequestLog).where(RequestLog.device_id == device_id))
    logs_deleted = result.rowcount

    # 清除 Redis 会话
    await delete_session(redis, device_id)

    await db.commit()

    return {
        "message": "数据已删除",
        "device_id": device_id,
        "request_logs_deleted": logs_deleted,
    }
