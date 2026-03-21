"""Test session management service (dd-intent-library.md §4.5)."""

import os
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.model_version import LibraryModelVersion
from app.models.test_session import IntentTestMessage, IntentTestSession
from app.services.inference.model_cache import ModelCache


async def create_session(
    db: AsyncSession, model_id: UUID, name: str, user_id: str,
) -> dict:
    model = await db.get(LibraryModelVersion, model_id)
    if not model:
        raise BusinessException("E50202", "模型版本不存在")

    session = IntentTestSession(
        library_id=model.library_id,
        model_id=model_id,
        name=name,
    )
    db.add(session)
    await db.flush()
    return _session_to_dict(session)


async def list_sessions(db: AsyncSession, model_id: UUID) -> list[dict]:
    query = (
        select(IntentTestSession)
        .where(IntentTestSession.model_id == model_id)
        .order_by(IntentTestSession.created_at.desc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_session_to_dict(s) for s in rows]


async def update_session(db: AsyncSession, session_id: UUID, name: str) -> dict:
    session = await _get_session(db, session_id)
    session.name = name
    await db.flush()
    return _session_to_dict(session)


async def delete_session(db: AsyncSession, session_id: UUID) -> None:
    session = await _get_session(db, session_id)
    await db.delete(session)
    await db.flush()


async def send_message(db: AsyncSession, session_id: UUID, content: str) -> list[dict]:
    session = await _get_session(db, session_id)

    model = await db.get(LibraryModelVersion, session.model_id)
    if not model or not model.artifact_uri:
        bot_content = "[模型未训练] 请先完成模型训练"
        result = {"intent": None, "confidence": 0.0, "slots": {}, "message": "模型未训练或无产物"}
    else:
        from app.core.config import resolve_artifact_path
        resolved = resolve_artifact_path(model.artifact_uri)
        model_dir = os.path.dirname(resolved) if resolved else None
        if not model_dir or not os.path.isdir(model_dir):
            bot_content = "[模型产物不存在] 请重新训练模型"
            result = {"intent": None, "confidence": 0.0, "slots": {}, "message": "模型产物路径无效"}
        else:
            try:
                engine = ModelCache.get_or_load(model_dir)
                intent_result = engine.classify_intent(content)
                slot_result = engine.extract_slots(content)

                bot_content = f"意图: {intent_result.intent} (置信度: {intent_result.confidence:.2%})"
                if slot_result.slots:
                    slot_str = ", ".join(f"{s['name']}={s['value']}" for s in slot_result.slots)
                    bot_content += f"\n槽位: {slot_str}"

                result = {
                    "intent": intent_result.intent,
                    "confidence": intent_result.confidence,
                    "slots": {s["name"]: s["value"] for s in slot_result.slots},
                    "all_scores": intent_result.all_scores[:5],
                    "latency_ms": intent_result.latency_ms + slot_result.latency_ms,
                }
            except Exception as e:
                bot_content = f"[推理错误] {str(e)[:200]}"
                result = {"intent": None, "confidence": 0.0, "slots": {}, "error": str(e)[:200]}

    user_msg = IntentTestMessage(
        session_id=session_id,
        role="user",
        content=content,
        result={},
    )
    db.add(user_msg)

    bot_msg = IntentTestMessage(
        session_id=session_id,
        role="assistant",
        content=bot_content,
        result=result,
    )
    db.add(bot_msg)

    session.message_count = session.message_count + 2
    await db.flush()

    return [_msg_to_dict(user_msg), _msg_to_dict(bot_msg)]


async def list_messages(
    db: AsyncSession, session_id: UUID, page: int = 1, page_size: int = 10,
) -> tuple[list[dict], int]:
    await _get_session(db, session_id)

    count_q = (
        select(func.count())
        .select_from(IntentTestMessage)
        .where(IntentTestMessage.session_id == session_id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(IntentTestMessage)
        .where(IntentTestMessage.session_id == session_id)
        .order_by(IntentTestMessage.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_msg_to_dict(m) for m in reversed(rows)], total


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_session(db: AsyncSession, session_id: UUID) -> IntentTestSession:
    session = await db.get(IntentTestSession, session_id)
    if not session:
        raise BusinessException("E50601", "测试会话不存在")
    return session


def _session_to_dict(s: IntentTestSession) -> dict:
    return {
        "id": str(s.id),
        "library_id": str(s.library_id),
        "model_id": str(s.model_id),
        "name": s.name,
        "message_count": s.message_count,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _msg_to_dict(m: IntentTestMessage) -> dict:
    return {
        "id": str(m.id),
        "session_id": str(m.session_id),
        "role": m.role,
        "content": m.content,
        "result": m.result,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }
