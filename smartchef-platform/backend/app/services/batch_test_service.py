"""Batch test execution and report generation."""
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis

from app.models.batch_test import BatchTestJob, BatchTestCase
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent
from app.schemas.batch_test import BatchTestCreate, BatchTestCaseInput
from app.services.nlu.pipeline import run_pipeline, PipelineConfig

logger = logging.getLogger(__name__)


async def create_and_run_batch_test(
    db: AsyncSession,
    redis: aioredis.Redis,
    data: BatchTestCreate,
    user_id: UUID | None = None,
) -> BatchTestJob:
    result = await db.execute(select(DialogProfile).where(DialogProfile.id == data.profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="对话方案不存在")

    job = BatchTestJob(
        name=data.name, profile_id=data.profile_id,
        status="running", total_cases=len(data.test_cases),
        created_by=user_id,
    )
    db.add(job)
    await db.flush()

    config = await _build_config(db, profile)

    passed = 0
    failed = 0
    total_latency = 0

    for tc in data.test_cases:
        device_id = f"batch_{job.id}"
        pipeline_result = await run_pipeline(
            db=db, redis=redis, text=tc.input_text,
            device_id=device_id, config=config,
        )

        is_passed = True
        if tc.expected_intent and pipeline_result.intent != tc.expected_intent:
            is_passed = False
        if tc.expected_domain and pipeline_result.domain != tc.expected_domain:
            is_passed = False

        case = BatchTestCase(
            job_id=job.id, input_text=tc.input_text,
            expected_intent=tc.expected_intent, expected_domain=tc.expected_domain,
            actual_intent=pipeline_result.intent, actual_domain=pipeline_result.domain,
            intent_confidence=pipeline_result.intent_confidence,
            latency_ms=pipeline_result.latency_ms,
            passed=is_passed, response_text=pipeline_result.response_text,
            debug_info=pipeline_result.debug_info,
        )
        db.add(case)
        total_latency += pipeline_result.latency_ms

        if is_passed:
            passed += 1
        else:
            failed += 1

    accuracy = passed / len(data.test_cases) if data.test_cases else 0
    avg_latency = total_latency / len(data.test_cases) if data.test_cases else 0

    report = _generate_report(
        accuracy, avg_latency, passed, failed,
        data.accuracy_threshold, data.latency_threshold_ms,
    )

    job.passed_cases = passed
    job.failed_cases = failed
    job.accuracy = round(accuracy, 4)
    job.avg_latency_ms = round(avg_latency, 2)
    job.status = "completed"
    job.report = report
    await db.flush()
    await db.refresh(job)

    return job


def _generate_report(accuracy, avg_latency, passed, failed, acc_threshold, lat_threshold):
    issues = []
    overall_pass = True

    if accuracy < acc_threshold:
        overall_pass = False
        issues.append({
            "type": "accuracy_below_threshold",
            "severity": "high",
            "message": f"准确率 {accuracy:.1%} 低于阈值 {acc_threshold:.1%}",
            "recommendation": "建议检查失败用例，补充训练数据或调整意图配置",
        })

    if avg_latency > lat_threshold:
        overall_pass = False
        issues.append({
            "type": "latency_above_threshold",
            "severity": "medium",
            "message": f"平均延迟 {avg_latency:.0f}ms 超过阈值 {lat_threshold}ms",
            "recommendation": "建议检查模型加载和网络延迟",
        })

    return {
        "overall_pass": overall_pass,
        "accuracy": round(accuracy, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "passed": passed,
        "failed": failed,
        "issues": issues,
    }


async def _build_config(db: AsyncSession, profile: DialogProfile) -> PipelineConfig:
    intents_result = await db.execute(
        select(Intent).options(selectinload(Intent.slots), selectinload(Intent.training_data))
    )
    intents = intents_result.scalars().unique().all()
    registered = []
    for intent in intents:
        registered.append({
            "intent_key": intent.intent_key,
            "display_name": intent.display_name,
            "category": intent.category,
            "slots": [
                {"slot_key": s.slot_key, "entity_type": s.entity_type,
                 "is_required": s.is_required, "prompt_text": s.prompt_text,
                 "display_name": s.display_name, "sort_order": s.sort_order}
                for s in (intent.slots or [])
            ],
            "training_texts": [td.text for td in (intent.training_data or [])],
        })

    persona_data = None
    if profile.persona:
        persona_data = {
            "name": profile.persona.name, "personality": profile.persona.personality,
            "tone_style": profile.persona.tone_style, "system_prompt": profile.persona.system_prompt,
        }

    return PipelineConfig(
        profile_id=profile.id, llm_provider=profile.llm_provider,
        llm_config=profile.llm_config or {}, persona_data=persona_data,
        routing_strategy=profile.routing_strategy,
        session_timeout_minutes=profile.session_timeout_minutes,
        registered_intents=registered,
        knowledge_base_ids=profile.knowledge_base_ids or [],
        has_knowledge_base=bool(profile.knowledge_base_ids),
    )
