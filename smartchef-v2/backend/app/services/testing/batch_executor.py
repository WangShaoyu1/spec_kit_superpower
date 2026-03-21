"""Batch test executor — iterates cases, calls NLU pipeline, writes TestRun results."""

import time
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.batch_test import BatchTest, TestCase, TestRun, TestRunAnalysis
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


async def execute_batch(db: AsyncSession, batch_id: uuid.UUID) -> BatchTest:
    batch = await batch_service.get_batch(db, batch_id)

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
