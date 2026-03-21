"""Intent test session routes (dd-intent-library.md §6.5)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import paginated_response, success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.schemas.intent_library import CreateSessionRequest, SendMessageRequest, UpdateSessionRequest
from app.services import test_session_service

router = APIRouter(tags=["intent-testing"])


@router.post("/models/{model_id}/test-sessions")
@require_capability("intent_library_write")
async def create_session(
    request: Request,
    model_id: UUID,
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await test_session_service.create_session(db, model_id, body.name, user.user_id)
    return success_response(data, status_code=201)


@router.get("/models/{model_id}/test-sessions")
async def list_sessions(
    request: Request,
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await test_session_service.list_sessions(db, model_id)
    return success_response(data)


@router.put("/test-sessions/{session_id}")
@require_capability("intent_library_write")
async def update_session(
    request: Request,
    session_id: UUID,
    body: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await test_session_service.update_session(db, session_id, body.name)
    return success_response(data)


@router.delete("/test-sessions/{session_id}")
@require_capability("intent_library_delete")
async def delete_session(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await test_session_service.delete_session(db, session_id)
    return success_response(None, msg="删除成功")


@router.post("/test-sessions/{session_id}/messages")
@require_capability("intent_library_write")
async def send_message(
    request: Request,
    session_id: UUID,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await test_session_service.send_message(db, session_id, body.content)
    return success_response(data)


@router.get("/test-sessions/{session_id}/messages")
async def list_messages(
    request: Request,
    session_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    items, total = await test_session_service.list_messages(
        db, session_id, page=page, page_size=page_size,
    )
    return paginated_response(items, total=total, page=page, page_size=page_size)
