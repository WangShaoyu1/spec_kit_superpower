"""T012: Device-facing dialog inference API."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException, success_response
from app.core.database import get_db
from app.core.config import get_settings
from app.models.request_log import RequestLog
from app.schemas.dialog import DialogRequest, DialogResponse
from app.services.nlu.pipeline import NLUPipeline
from app.services.version.loader import VersionLoader

router = APIRouter(tags=["dialog"])

_pipeline = NLUPipeline()
_version_loader = VersionLoader()


def _verify_device_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    settings = get_settings()
    device_key = getattr(settings, "DEVICE_API_KEY", "")
    if not device_key:
        return
    if x_api_key != device_key:
        raise BusinessException("DIALOG_002", "Device API key 无效或缺失", http_status=401)


@router.post("/dialog", dependencies=[Depends(_verify_device_api_key)])
async def dialog_inference(request: DialogRequest, db: AsyncSession = Depends(get_db)):
    """Device-facing dialog endpoint.

    1. Load profile runtime config
    2. Assign / resume session (placeholder)
    3. Run NLU pipeline
    4. Persist RequestLog
    5. Return structured response
    """
    start = time.perf_counter()

    profile_config = await _version_loader.load_profile_runtime(db, request.profile_id)
    if profile_config is None:
        raise BusinessException("DIALOG_001", f"Profile {request.profile_id} not found")

    session_id = request.session_id or str(uuid.uuid4())

    nlu_result = await _pipeline.process(
        text=request.text,
        profile_config=profile_config,
        session_context={"session_id": session_id, "device_id": request.device_id},
    )

    latency_ms = round((time.perf_counter() - start) * 1000)

    log_entry = RequestLog(
        request_id=str(uuid.uuid4()),
        session_id=session_id,
        device_id=request.device_id,
        input_text=request.text,
        domain=nlu_result.get("domain"),
        intent=nlu_result.get("intent"),
        slots=nlu_result.get("slots", {}),
        confidence=nlu_result.get("confidence"),
        latency_ms=latency_ms,
        response_text=nlu_result.get("response_text"),
        profile_id=request.profile_id,
        status="success",
    )
    db.add(log_entry)

    response = DialogResponse(
        session_id=session_id,
        domain=nlu_result["domain"],
        intent=nlu_result.get("intent"),
        slots=nlu_result.get("slots", {}),
        confidence=nlu_result.get("confidence", 0.0),
        response_text=nlu_result["response_text"],
        debug=nlu_result.get("debug", {}),
    )
    return success_response(response.model_dump())
