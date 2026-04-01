import json

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crypto import encrypt_json
from app.api.dialog_profile import (
    get_published_profile,
    process_dialog_turn,
    upsert_device_session,
    write_request_log,
)
from app.dependencies import ApiError, get_current_user, get_db, response_envelope
from app.models import DialogProfileLibraryBinding, UserAccount


router = APIRouter(prefix="/runtime", tags=["runtime"])


class RuntimeMessagePayload(BaseModel):
    text: str
    device_context: dict = {}


@router.post("/devices/{device_id}/messages")
def send_runtime_message(
    device_id: str,
    payload: RuntimeMessagePayload,
    request: Request,
    _: UserAccount = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    if not payload.text.strip():
        raise ApiError(422, "RUNTIME-422-MESSAGE", "请输入设备请求文本")

    profile = get_published_profile(session)
    bindings = session.execute(
        select(DialogProfileLibraryBinding)
        .where(DialogProfileLibraryBinding.profile_id == profile.id)
        .order_by(DialogProfileLibraryBinding.priority.asc())
    ).scalars().all()

    merged_context = {
        **payload.device_context,
        "device_id": device_id,
    }
    device_session = upsert_device_session(
        session,
        device_id=device_id,
        profile=profile,
        device_context=merged_context,
    )
    turn = process_dialog_turn(
        profile=profile,
        bindings=bindings,
        text=payload.text.strip(),
        device_context=merged_context,
    )
    device_session.device_context_json = encrypt_json(merged_context)
    write_request_log(
        session,
        request_id=request.state.request_id,
        device_id=device_id,
        session_id=device_session.id,
        profile_id=profile.id,
        text=payload.text.strip(),
        route=turn["route"],
        intent=turn["intent"],
        latency_ms=turn["response_time_ms"],
        device_context=merged_context,
        debug_trace=turn["debug_trace"],
        profile_version=profile.publish_version,
    )
    session.commit()

    return response_envelope(
        request,
        {
            "domain_type": turn["route"],
            "intent": turn["debug_trace"]["intent"],
            "slots": turn["slots"],
            "reply_text": turn["response_text"],
            "confidence": turn["debug_trace"]["intent"]["confidence"],
            "session_id": device_session.id,
            "need_clarification": False,
            "latency_ms": turn["response_time_ms"],
            "profile_version": profile.publish_version,
        },
    )
