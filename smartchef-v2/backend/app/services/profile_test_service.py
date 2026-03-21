"""Profile test session CRUD + message send service."""

import time
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.dialog_profile import (
    DialogProfile, ProfileTestMessage, ProfileTestSession,
)
from app.services.nlu_pipeline import classify_message


async def list_sessions(db: AsyncSession, profile_id: UUID) -> list[dict]:
    await _ensure_profile(db, profile_id)
    query = (
        select(ProfileTestSession)
        .where(ProfileTestSession.profile_id == profile_id)
        .order_by(ProfileTestSession.updated_at.desc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_session_dict(s) for s in rows]


async def create_session(db: AsyncSession, profile_id: UUID, name: str) -> dict:
    await _ensure_profile(db, profile_id)
    session = ProfileTestSession(profile_id=profile_id, name=name)
    db.add(session)
    await db.flush()
    return _session_dict(session)


async def update_session(db: AsyncSession, session_id: UUID, name: str) -> dict:
    session = await db.get(ProfileTestSession, session_id)
    if not session:
        raise BusinessException("E40401", "测试会话不存在")
    session.name = name
    await db.flush()
    return _session_dict(session)


async def delete_session(db: AsyncSession, session_id: UUID) -> None:
    session = await db.get(ProfileTestSession, session_id)
    if not session:
        raise BusinessException("E40401", "测试会话不存在")
    await db.delete(session)
    await db.flush()


async def list_messages(db: AsyncSession, session_id: UUID) -> list[dict]:
    session = await db.get(ProfileTestSession, session_id)
    if not session:
        raise BusinessException("E40401", "测试会话不存在")

    query = (
        select(ProfileTestMessage)
        .where(ProfileTestMessage.session_id == session_id)
        .order_by(ProfileTestMessage.created_at.asc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_message_dict(m) for m in rows]


async def send_message(db: AsyncSession, session_id: UUID, content: str) -> dict:
    session = await db.get(ProfileTestSession, session_id)
    if not session:
        raise BusinessException("E40401", "测试会话不存在")

    user_msg = ProfileTestMessage(
        session_id=session_id,
        role="user",
        content=content,
        debug_info={},
    )
    db.add(user_msg)

    t0 = time.time()
    nlu_result = classify_message(content)
    latency_ms = round((time.time() - t0) * 1000, 1)

    debug_info = {
        **nlu_result,
        "latency_ms": latency_ms,
    }

    domain = nlu_result.get("domain", "chitchat")
    if domain == "command":
        reply = f"[指令识别] 意图: {nlu_result.get('intent', 'unknown')}，置信度: {nlu_result.get('confidence', 0):.2f}"
    elif domain == "knowledge":
        reply = "[知识问答] 这是一个知识库查询，正在检索相关文档..."
    else:
        reply = "你好！我是 SmartChef 助手，有什么可以帮你的？"

    assistant_msg = ProfileTestMessage(
        session_id=session_id,
        role="assistant",
        content=reply,
        debug_info=debug_info,
    )
    db.add(assistant_msg)

    session.message_count = (
        await db.execute(
            select(func.count())
            .select_from(ProfileTestMessage)
            .where(ProfileTestMessage.session_id == session_id)
        )
    ).scalar() or 0
    session.message_count += 2  # user + assistant just added

    await db.flush()

    return {
        "user_message": _message_dict(user_msg),
        "assistant_message": _message_dict(assistant_msg),
    }


async def _ensure_profile(db: AsyncSession, profile_id: UUID) -> DialogProfile:
    profile = await db.get(DialogProfile, profile_id)
    if not profile:
        raise BusinessException("E40101", "对话方案不存在")
    return profile


def _session_dict(s: ProfileTestSession) -> dict:
    return {
        "id": str(s.id),
        "profile_id": str(s.profile_id),
        "name": s.name,
        "message_count": s.message_count,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _message_dict(m: ProfileTestMessage) -> dict:
    return {
        "id": str(m.id),
        "session_id": str(m.session_id),
        "role": m.role,
        "content": m.content,
        "debug_info": m.debug_info,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }
