import secrets
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto import decrypt_json
from app.dependencies import ApiError, get_current_user, get_db, response_envelope, utc_now
from app.models import DevicePrivacyDeleteRequest, DeviceSession, RequestLog, UserAccount


router = APIRouter(prefix="/privacy", tags=["privacy"])


class DeleteRequestPayload(BaseModel):
    reason: str = ""


class DeleteConfirmPayload(BaseModel):
    confirmation_token: str


def require_admin(user: UserAccount):
    if user.role_key != "admin":
        raise ApiError(403, "AUTH-403", "仅管理员可执行设备隐私操作")


@router.get("/devices/{device_id}/export")
def export_device_data(
    device_id: str,
    request: Request,
    user: UserAccount = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    require_admin(user)
    request_logs = session.execute(
        select(RequestLog).where(RequestLog.device_id == device_id).order_by(RequestLog.created_at.asc())
    ).scalars().all()
    device_sessions = session.execute(
        select(DeviceSession).where(DeviceSession.device_id == device_id).order_by(DeviceSession.created_at.asc())
    ).scalars().all()
    if not request_logs and not device_sessions:
        raise ApiError(404, "PRIVACY-404-DEVICE", "目标设备暂无可导出数据")

    return response_envelope(
        request,
        {
            "device_id": device_id,
            "request_logs": [
                {
                    "request_id": item.request_id,
                    "session_id": item.session_id,
                    "route_type": item.route_type,
                    "intent_name": item.intent_name,
                    "latency_ms": item.latency_ms,
                    "request": decrypt_json(item.request_json, {}),
                    "response": decrypt_json(item.response_json, {}),
                    "created_at": item.created_at.isoformat() + "Z",
                }
                for item in request_logs
            ],
            "device_sessions": [
                {
                    "session_id": item.id,
                    "profile_id": item.profile_id,
                    "profile_version": item.profile_version,
                    "device_context": decrypt_json(item.device_context_json, {}),
                    "last_message_at": item.last_message_at.isoformat() + "Z" if item.last_message_at else None,
                    "expires_at": item.expires_at.isoformat() + "Z" if item.expires_at else None,
                }
                for item in device_sessions
            ],
        },
    )


@router.post("/devices/{device_id}/delete-request")
def create_delete_request(
    device_id: str,
    payload: DeleteRequestPayload,
    request: Request,
    user: UserAccount = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    require_admin(user)
    now = utc_now()
    confirmation = DevicePrivacyDeleteRequest(
        id=uuid.uuid4().hex,
        device_id=device_id,
        requested_by=user.id,
        reason=payload.reason.strip(),
        confirmation_token=secrets.token_urlsafe(24),
        expires_at=now + timedelta(seconds=request.app.state.settings.privacy_confirmation_ttl_seconds),
    )
    session.add(confirmation)
    session.commit()
    return response_envelope(
        request,
        {
            "device_id": device_id,
            "confirmation_token": confirmation.confirmation_token,
            "expires_at": confirmation.expires_at.isoformat() + "Z",
        },
    )


@router.delete("/devices/{device_id}")
def delete_device_data(
    device_id: str,
    payload: DeleteConfirmPayload,
    request: Request,
    user: UserAccount = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    require_admin(user)
    confirmation = session.execute(
        select(DevicePrivacyDeleteRequest)
        .where(DevicePrivacyDeleteRequest.device_id == device_id)
        .order_by(DevicePrivacyDeleteRequest.created_at.desc())
    ).scalars().first()
    if confirmation is None or confirmation.confirmation_token != payload.confirmation_token:
        raise ApiError(409, "PRIVACY-409-CONFIRM", "删除确认令牌无效")
    if confirmation.expires_at < utc_now():
        raise ApiError(409, "PRIVACY-409-CONFIRM", "删除确认令牌已过期")
    if confirmation.consumed_at is not None:
        raise ApiError(409, "PRIVACY-409-CONFIRM", "删除确认令牌已使用")

    request_logs = session.execute(select(RequestLog).where(RequestLog.device_id == device_id)).scalars().all()
    device_sessions = session.execute(select(DeviceSession).where(DeviceSession.device_id == device_id)).scalars().all()
    for item in request_logs:
        session.delete(item)
    for item in device_sessions:
        session.delete(item)
    confirmation.consumed_at = utc_now()
    session.commit()
    return response_envelope(
        request,
        {
            "device_id": device_id,
            "deleted_request_logs": len(request_logs),
            "deleted_device_sessions": len(device_sessions),
        },
    )
