"""批量测试执行器：异步并发执行测试用例，收集结果并生成报告。"""
import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis

from app.core.database import async_session_factory
from app.models.batch_test import BatchTestJob, BatchTestCase
from app.models.dialog_profile import DialogProfile
from app.models.intent import Intent
from app.services.nlu.pipeline import run_pipeline, PipelineConfig, PipelineResult

logger = logging.getLogger(__name__)

DEFAULT_CONCURRENCY = 10

__all__ = ["execute_batch_test"]


async def execute_batch_test(
    db: AsyncSession,
    redis: aioredis.Redis,
    job_id: UUID,
    concurrency: int = DEFAULT_CONCURRENCY,
) -> BatchTestJob:
    """
    执行批量测试任务。

    流程：加载用例 → 并发调用 NLU Pipeline → 比较预期/实际 → 更新统计报告。
    每个用例使用独立数据库会话执行 Pipeline，避免并发冲突。
    """
    job = await _load_job(db, job_id)
    profile = await _load_profile(db, job.profile_id)
    registered_intents = await _load_registered_intents(db, profile)
    config = _build_pipeline_config(profile, registered_intents)
    cases = await _load_cases(db, job_id)

    job.status = "running"
    job.total_cases = len(cases)
    await db.flush()

    # 使用信号量控制并发度，每个用例在独立 DB 会话中调用 Pipeline
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        _execute_single_case(
            redis=redis,
            case_id=case.id,
            input_text=case.input_text,
            expected_intent=case.expected_intent,
            expected_domain=case.expected_domain,
            job_id=case.job_id,
            config=config,
            semaphore=semaphore,
        )
        for case in cases
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 将执行结果写回用例记录
    passed_count = 0
    failed_count = 0
    total_latency = 0.0

    for case, result in zip(cases, results):
        if isinstance(result, Exception):
            logger.error("用例执行异常 case_id=%s: %s", case.id, result)
            case.passed = False
            case.debug_info = {"error": str(result)}
            failed_count += 1
            continue

        case.actual_intent = result["actual_intent"]
        case.actual_domain = result["actual_domain"]
        case.intent_confidence = result["intent_confidence"]
        case.latency_ms = result["latency_ms"]
        case.passed = result["passed"]
        case.response_text = result["response_text"]
        case.debug_info = result["debug_info"]

        if result["passed"]:
            passed_count += 1
        else:
            failed_count += 1
        total_latency += result["latency_ms"] or 0

    executed = passed_count + failed_count
    job.passed_cases = passed_count
    job.failed_cases = failed_count
    job.accuracy = passed_count / executed if executed > 0 else 0.0
    job.avg_latency_ms = total_latency / executed if executed > 0 else 0.0
    job.status = "completed"
    job.report = _build_report_summary(job, cases)

    await db.flush()
    await db.refresh(job)
    return job


# ── 数据加载 ──────────────────────────────────────────────────


async def _load_job(db: AsyncSession, job_id: UUID) -> BatchTestJob:
    """加载批量测试任务，不存在则抛异常。"""
    result = await db.execute(
        select(BatchTestJob).where(BatchTestJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError(f"批量测试任务不存在: {job_id}")
    return job


async def _load_profile(db: AsyncSession, profile_id: UUID) -> DialogProfile:
    """加载对话方案及关联人设。"""
    result = await db.execute(
        select(DialogProfile)
        .options(selectinload(DialogProfile.persona))
        .where(DialogProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise ValueError(f"对话方案不存在: {profile_id}")
    return profile


async def _load_registered_intents(
    db: AsyncSession, profile: DialogProfile
) -> list[dict]:
    """加载方案关联的全部意图、槽位、训练数据。"""
    profile_intent_ids = profile.intent_ids or []
    query = select(Intent).options(
        selectinload(Intent.slots),
        selectinload(Intent.training_data),
    )
    if profile_intent_ids:
        query = query.where(Intent.id.in_(profile_intent_ids))
    result = await db.execute(query)
    intents = result.scalars().unique().all()

    return [
        {
            "intent_key": intent.intent_key,
            "display_name": intent.display_name,
            "category": intent.category,
            "slots": [
                {
                    "slot_key": s.slot_key,
                    "entity_type": s.entity_type,
                    "is_required": s.is_required,
                    "prompt_text": s.prompt_text,
                    "display_name": s.display_name,
                    "sort_order": s.sort_order,
                }
                for s in (intent.slots or [])
            ],
            "training_texts": [td.text for td in (intent.training_data or [])],
        }
        for intent in intents
    ]


async def _load_cases(db: AsyncSession, job_id: UUID) -> list[BatchTestCase]:
    """加载任务下所有测试用例。"""
    result = await db.execute(
        select(BatchTestCase).where(BatchTestCase.job_id == job_id)
    )
    return list(result.scalars().all())


# ── Pipeline 配置 ─────────────────────────────────────────────


def _build_pipeline_config(
    profile: DialogProfile, registered_intents: list[dict]
) -> PipelineConfig:
    """根据对话方案和意图列表构建 PipelineConfig。"""
    persona_data = None
    if profile.persona:
        persona_data = {
            "name": profile.persona.name,
            "personality": profile.persona.personality,
            "tone_style": profile.persona.tone_style,
            "system_prompt": profile.persona.system_prompt,
        }
    return PipelineConfig(
        profile_id=profile.id,
        llm_provider=profile.llm_provider,
        llm_config=profile.llm_config or {},
        persona_data=persona_data,
        routing_strategy=profile.routing_strategy,
        session_timeout_minutes=profile.session_timeout_minutes,
        registered_intents=registered_intents,
        knowledge_base_ids=profile.knowledge_base_ids or [],
        has_knowledge_base=bool(profile.knowledge_base_ids),
    )


# ── 单用例执行 ────────────────────────────────────────────────


async def _execute_single_case(
    redis: aioredis.Redis,
    case_id: UUID,
    input_text: str,
    expected_intent: str | None,
    expected_domain: str | None,
    job_id: UUID,
    config: PipelineConfig,
    semaphore: asyncio.Semaphore,
) -> dict:
    """在独立数据库会话中执行单个用例的 NLU Pipeline 调用。"""
    async with semaphore:
        device_id = f"batch_{job_id}_{case_id}"
        async with async_session_factory() as case_db:
            pipeline_result = await run_pipeline(
                db=case_db,
                redis=redis,
                text=input_text,
                device_id=device_id,
                config=config,
            )

        passed = _check_passed(expected_domain, expected_intent, pipeline_result)
        return {
            "actual_intent": pipeline_result.intent,
            "actual_domain": pipeline_result.domain,
            "intent_confidence": pipeline_result.intent_confidence,
            "latency_ms": pipeline_result.latency_ms,
            "passed": passed,
            "response_text": pipeline_result.response_text,
            "debug_info": pipeline_result.debug_info,
        }


def _check_passed(
    expected_domain: str | None,
    expected_intent: str | None,
    result: PipelineResult,
) -> bool:
    """比较预期和实际结果，全部匹配视为通过。"""
    if expected_domain and result.domain != expected_domain:
        return False
    if expected_intent and result.intent != expected_intent:
        return False
    return True


# ── 报告生成 ──────────────────────────────────────────────────


def _build_report_summary(
    job: BatchTestJob, cases: list[BatchTestCase]
) -> dict:
    """构建测试报告：总体摘要 + 域维度统计 + 意图维度统计。"""
    domain_stats: dict[str, dict] = {}
    intent_stats: dict[str, dict] = {}

    for case in cases:
        _accumulate(domain_stats, case.expected_domain or "unknown", case.passed)
        _accumulate(intent_stats, case.expected_intent or "unknown", case.passed)

    for stats in (*domain_stats.values(), *intent_stats.values()):
        stats["accuracy"] = (
            stats["passed"] / stats["total"] if stats["total"] else 0.0
        )

    return {
        "summary": {
            "total_cases": job.total_cases,
            "passed_cases": job.passed_cases,
            "failed_cases": job.failed_cases,
            "accuracy": job.accuracy,
            "avg_latency_ms": job.avg_latency_ms,
        },
        "domain_stats": domain_stats,
        "intent_stats": intent_stats,
    }


def _accumulate(stats: dict, key: str, passed: bool | None) -> None:
    """累加域/意图维度的通过/失败计数。"""
    if key not in stats:
        stats[key] = {"total": 0, "passed": 0, "failed": 0}
    stats[key]["total"] += 1
    if passed:
        stats[key]["passed"] += 1
    else:
        stats[key]["failed"] += 1
