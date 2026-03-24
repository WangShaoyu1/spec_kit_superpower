"""Batch test executor — iterates cases, calls NLU pipeline, writes TestRun results."""

import os
import time
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.core.config import resolve_artifact_path
from app.models.batch_test import BatchTest, TestCase, TestRun, TestRunAnalysis
from app.models.model_version import LibraryModelVersion
from app.services.inference.model_cache import ModelCache
from app.services.testing import batch_service


async def _call_nlu_pipeline(input_text: str, profile_id: uuid.UUID | None) -> dict:
    """Placeholder for actual NLU pipeline call.

    Replace with real NLU invocation when the pipeline module is integrated.
    """
    return {
        "domain": "command",
        "intent": "unknown",
        "slots": {},
        "confidence": 0.0,
    }


async def _infer_with_model(db: AsyncSession, model_id: uuid.UUID, input_text: str) -> dict:
    model = await db.get(LibraryModelVersion, model_id)
    if not model or not model.artifact_uri:
        raise BusinessException("E50106", "批量测试绑定的模型不存在或尚未训练")

    resolved = resolve_artifact_path(model.artifact_uri)
    model_dir = os.path.dirname(resolved) if resolved else None
    if not model_dir or not os.path.isdir(model_dir):
        raise BusinessException("E50107", "批量测试绑定的模型产物不存在，请重新训练")

    engine = ModelCache.get_or_load(model_dir)
    intent_result = engine.classify_intent(input_text)
    slot_result = engine.extract_slots(input_text)

    return {
        "domain": "command",
        "intent": intent_result.intent,
        "slots": {s["name"]: s["value"] for s in slot_result.slots},
        "confidence": intent_result.confidence,
    }


async def execute_batch(db: AsyncSession, batch_id: uuid.UUID) -> BatchTest:
    batch = await batch_service.get_batch(db, batch_id)

    if batch.model_id is None and batch.profile_id is None:
        raise BusinessException("E50104", "批量测试必须绑定 model_id 或 profile_id")

    if batch.total_cases == 0:
        raise BusinessException("E50103", "没有测试用例，无法执行")

    if batch.status not in ("ready", "completed", "failed"):
        raise BusinessException("E50102", f"当前状态 {batch.status} 不允许执行")

    await batch_service.transition_status(db, batch, "running")
    batch.completed_cases = 0
    batch.accuracy = None
    batch.precision_score = None
    batch.recall_score = None
    batch.p99_latency_ms = None
    await db.execute(delete(TestRun).where(TestRun.batch_id == batch_id))
    await db.execute(delete(TestRunAnalysis).where(TestRunAnalysis.batch_id == batch_id))
    await db.flush()

    cases_result = await db.execute(
        select(TestCase)
        .where(TestCase.batch_id == batch_id)
        .order_by(TestCase.sort_order, TestCase.created_at)
    )
    cases = cases_result.scalars().all()

    try:
        for case in cases:
            start = time.monotonic()
            try:
                if batch.model_id is not None:
                    nlu_result = await _infer_with_model(db, batch.model_id, case.input_text)
                else:
                    nlu_result = await _call_nlu_pipeline(case.input_text, batch.profile_id)
                latency = int((time.monotonic() - start) * 1000)

                actual_domain = nlu_result.get("domain")
                actual_intent = nlu_result.get("intent")
                actual_slots = nlu_result.get("slots", {})
                confidence = nlu_result.get("confidence")

                is_domain_hit = (
                    actual_domain == case.expected_domain
                    if case.expected_domain else None
                )
                is_intent_hit = (
                    actual_intent == case.expected_intent
                    if case.expected_intent else None
                )

                run = TestRun(
                    id=uuid.uuid4(),
                    batch_id=batch_id,
                    case_id=case.id,
                    actual_domain=actual_domain,
                    actual_intent=actual_intent,
                    actual_slots=actual_slots,
                    confidence=confidence,
                    is_domain_hit=is_domain_hit,
                    is_intent_hit=is_intent_hit,
                    latency_ms=latency,
                )
                db.add(run)

            except Exception as e:
                latency = int((time.monotonic() - start) * 1000)
                run = TestRun(
                    id=uuid.uuid4(),
                    batch_id=batch_id,
                    case_id=case.id,
                    latency_ms=latency,
                    error_message=str(e),
                )
                db.add(run)

            batch.completed_cases += 1
            await db.flush()

        await batch_service.transition_status(db, batch, "completed")

    except Exception:
        await batch_service.transition_status(db, batch, "failed")
        raise

    await db.refresh(batch)
    return batch
