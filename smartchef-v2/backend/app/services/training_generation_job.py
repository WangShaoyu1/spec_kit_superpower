"""异步训练集相似问生成任务（Redis 状态 + asyncio.create_task 执行）。"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from app.core.api_response import BusinessException
from app.core.database import async_session_factory, init_db
from app.core.redis import get_redis
from app.services import data_generation_service

logger = logging.getLogger(__name__)

JOB_KEY_PREFIX = "training_gen:job:"
JOB_TTL_SECONDS = 86400  # 24h


def _job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


async def save_job_state(job_id: str, state: dict[str, Any]) -> None:
    redis = get_redis()
    await redis.setex(
        _job_key(job_id),
        JOB_TTL_SECONDS,
        json.dumps(state, ensure_ascii=False),
    )


async def load_job_state(job_id: str) -> dict[str, Any] | None:
    redis = get_redis()
    raw = await redis.get(_job_key(job_id))
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


async def merge_job_state(job_id: str, partial: dict[str, Any]) -> None:
    cur = await load_job_state(job_id) or {}
    cur.update(partial)
    await save_job_state(job_id, cur)


async def run_training_generation_job(job_id: str, library_id: UUID, config: dict) -> None:
    """由路由内 asyncio.create_task 调度；独立 Session，按意图 commit。"""
    logger.info("training job %s starting library_id=%s", job_id, library_id)
    try:
        if async_session_factory is None:
            await init_db()
        if async_session_factory is None:
            raise RuntimeError("async_session_factory 未初始化，请确认 lifespan 中已 init_db")

        async def on_progress(update: dict[str, Any]) -> None:
            await merge_job_state(job_id, update)

        await merge_job_state(
            job_id,
            {
                "status": "running",
                "message": "正在生成相似问…",
            },
        )
        async with async_session_factory() as session:
            result = await data_generation_service.generate_training_data(
                session,
                library_id,
                config,
                progress_callback=on_progress,
            )
        await merge_job_state(
            job_id,
            {
                "status": "completed",
                "message": "完成",
                **result,
            },
        )
    except BusinessException as e:
        logger.warning("training job %s business error: %s %s", job_id, e.error_code, e.error_msg)
        try:
            await merge_job_state(
                job_id,
                {
                    "status": "failed",
                    "error_code": e.error_code,
                    "error": e.error_msg,
                    "message": e.error_msg,
                },
            )
        except Exception:
            logger.exception("training job %s: failed to persist BusinessException to redis", job_id)
    except Exception as e:
        logger.exception("training job %s failed", job_id)
        try:
            await merge_job_state(
                job_id,
                {
                    "status": "failed",
                    "error": str(e),
                    "message": str(e),
                },
            )
        except Exception:
            logger.exception("training job %s: failed to persist error to redis", job_id)
