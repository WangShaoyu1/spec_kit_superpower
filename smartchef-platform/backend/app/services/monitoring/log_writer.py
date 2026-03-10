"""请求日志记录：记录 /dialog 请求的完整处理链路。"""
import uuid
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog


def _ensure_dict(val):
    """确保槽位、知识命中等为可 JSON 序列化的 dict。"""
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    return dict(val)


async def write_request_log(
    db: AsyncSession,
    *,
    request_id: str | None = None,
    device_id: str,
    session_id: str | None,
    input_text: str,
    route_result: str,
    route_confidence: float | None = None,
    intent: str | None = None,
    intent_confidence: float | None = None,
    slots: dict | None = None,
    response_text: str,
    knowledge_hit: dict | None = None,
    device_context: dict | None = None,
    latency_ms: int,
    is_error: bool = False,
    error_detail: str | None = None,
    language: str = "zh",
    version_id: UUID | None = None,
) -> RequestLog:
    """
    记录每次 /dialog 请求的完整链路。

    字段说明（符合 FR-033）：
    - 请求ID、设备ID、会话ID、文本输入
    - 路由结果、意图、槽位、响应、延迟、时间戳
    - 扩展信息存于 extra（request_id、route_confidence、knowledge_hit、device_context 等）
    """
    rid = request_id or str(uuid.uuid4())
    extra: dict = {
        "request_id": rid,
        "route_confidence": route_confidence,
        "slots_extracted": _ensure_dict(slots),
        "knowledge_hit": _ensure_dict(knowledge_hit),
        "device_context": _ensure_dict(device_context),
        "is_error": is_error,
        "error_detail": error_detail,
    }
    if version_id:
        extra["version_id"] = str(version_id)

    log = RequestLog(
        device_id=device_id,
        session_id=session_id,
        input_text=input_text,
        domain=route_result,
        intent=intent,
        response_text=response_text or "",
        latency_ms=latency_ms,
        intent_confidence=intent_confidence,
        language=language,
        extra=extra,
    )
    db.add(log)
    await db.flush()
    return log
