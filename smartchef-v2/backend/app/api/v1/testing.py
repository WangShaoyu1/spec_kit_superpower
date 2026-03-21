"""Profile test chat API routes — sessions + messages."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.schemas.profile import (
    CreateTestSessionRequest,
    SendTestMessageRequest,
    UpdateTestSessionRequest,
)
from app.services import profile_test_service

router = APIRouter(tags=["testing"])


@router.post("/profiles/{profile_id}/test-sessions")
async def create_session(
    request: Request,
    profile_id: UUID,
    body: CreateTestSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await profile_test_service.create_session(db, profile_id, body.name)
    return success_response(data, status_code=201)


@router.get("/profiles/{profile_id}/test-sessions")
async def list_sessions(
    request: Request,
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await profile_test_service.list_sessions(db, profile_id)
    return success_response(data)


@router.put("/test-sessions/{session_id}")
async def update_session(
    request: Request,
    session_id: UUID,
    body: UpdateTestSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await profile_test_service.update_session(db, session_id, body.name)
    return success_response(data)


@router.delete("/test-sessions/{session_id}")
async def delete_session(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    await profile_test_service.delete_session(db, session_id)
    return success_response(None, msg="删除成功")


@router.post("/test-sessions/{session_id}/messages")
async def send_message(
    request: Request,
    session_id: UUID,
    body: SendTestMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await profile_test_service.send_message(db, session_id, body.content)
    return success_response(data)


@router.get("/test-sessions/{session_id}/messages")
async def list_messages(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await profile_test_service.list_messages(db, session_id)
    return success_response(data)
