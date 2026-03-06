"""Device session manager: Redis Hash + TTL management."""
import json
import uuid
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

SESSION_KEY_PREFIX = "session:"


def _session_key(device_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{device_id}"


async def get_session(redis: aioredis.Redis, device_id: str) -> dict | None:
    key = _session_key(device_id)
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None


async def create_session(
    redis: aioredis.Redis,
    device_id: str,
    version_id: str | None = None,
    timeout_minutes: int = 10,
) -> dict:
    session = {
        "session_id": str(uuid.uuid4()),
        "device_id": device_id,
        "version_id": version_id,
        "state": "IDLE",
        "current_domain": None,
        "dialog_history": [],
        "entity_stack": [],
        "pending_slots": None,
        "active_intent": None,
        "filled_slots": {},
        "unrecognized_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }
    key = _session_key(device_id)
    await redis.set(key, json.dumps(session, ensure_ascii=False), ex=timeout_minutes * 60)
    return session


async def update_session(
    redis: aioredis.Redis,
    device_id: str,
    session: dict,
    timeout_minutes: int = 10,
) -> None:
    session["last_active_at"] = datetime.now(timezone.utc).isoformat()
    key = _session_key(device_id)
    await redis.set(key, json.dumps(session, ensure_ascii=False), ex=timeout_minutes * 60)


async def delete_session(redis: aioredis.Redis, device_id: str) -> None:
    key = _session_key(device_id)
    await redis.delete(key)


async def add_dialog_turn(
    session: dict,
    user_text: str,
    route: str,
    intent: str | None,
    slots: dict | None,
    response: str,
) -> dict:
    turn = {
        "turn": len(session["dialog_history"]) + 1,
        "user_text": user_text,
        "route": route,
        "intent": intent,
        "slots": slots,
        "response": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    session["dialog_history"].append(turn)

    if slots:
        for key, value in slots.items():
            session["entity_stack"].append({
                "type": key,
                "value": value,
                "turn": turn["turn"],
            })
        if len(session["entity_stack"]) > 20:
            session["entity_stack"] = session["entity_stack"][-20:]

    return session


async def clear_all_sessions(redis: aioredis.Redis) -> int:
    cursor = 0
    count = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=f"{SESSION_KEY_PREFIX}*", count=100)
        if keys:
            await redis.delete(*keys)
            count += len(keys)
        if cursor == 0:
            break
    logger.info(f"Cleared {count} device sessions")
    return count
