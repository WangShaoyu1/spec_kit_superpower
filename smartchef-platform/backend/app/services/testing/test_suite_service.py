"""测试套件服务：创建套件、生成用例、执行、报告。"""
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import redis.asyncio as aioredis

from app.models.test_suite import TestSuite, TestCase, TestReport
from app.models.dialog_profile import DialogProfile
from app.schemas.batch_test import BatchTestCreate, BatchTestCaseInput
from app.schemas.test_suite import TestSuiteCreate
from app.services.batch_test_service import create_and_run_batch_test
from app.services.testing.case_generator import generate_test_cases

# 若 analyzer 存在则导入，否则使用 stub
try:
    from app.services.testing.analyzer import analyze_report
except ImportError:
    def analyze_report(report_data: dict) -> dict:
        """Stub：报告分析（待实现）。"""
        return {
            "summary": "分析功能待实现",
            "intent_accuracy_ranking": [],
            "confusion_matrix": {},
            "failure_analysis": [],
            "optimization_suggestions": [],
        }


async def create_suite(
    db: AsyncSession,
    body: TestSuiteCreate,
    user_id: UUID | None = None,
) -> TestSuite:
    """创建测试套件。"""
    result = await db.execute(select(DialogProfile).where(DialogProfile.id == body.profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="对话方案不存在")

    suite = TestSuite(
        name=body.name,
        profile_id=body.profile_id,
        created_by=user_id,
    )
    db.add(suite)
    await db.flush()
    await db.refresh(suite)
    return suite


async def list_suites(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[TestSuite], int]:
    """列出测试套件（含用例数量）。"""
    count_q = select(func.count()).select_from(TestSuite)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(TestSuite)
        .order_by(TestSuite.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    suites = list(result.scalars().all())

    # 加载用例数量
    for suite in suites:
        case_count_q = select(func.count()).select_from(TestCase).where(TestCase.suite_id == suite.id)
        suite._case_count = (await db.execute(case_count_q)).scalar() or 0

    return suites, total


async def get_suite(db: AsyncSession, suite_id: UUID) -> TestSuite | None:
    """获取套件详情（含用例）。"""
    result = await db.execute(
        select(TestSuite)
        .options(selectinload(TestSuite.cases))
        .where(TestSuite.id == suite_id)
    )
    return result.scalar_one_or_none()


async def generate_cases_for_suite(
    db: AsyncSession,
    suite_id: UUID,
    user_id: UUID | None = None,
) -> int:
    """
    为套件生成测试用例。
    使用 case_generator 生成，将结果写入套件的 TestCase。
    返回生成的用例数量。
    """
    suite = await get_suite(db, suite_id)
    if not suite:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="测试套件不存在")

    # 删除已有用例
    await db.execute(delete(TestCase).where(TestCase.suite_id == suite_id))

    # 调用 case_generator：它创建 BatchTestJob + BatchTestCase
    # 我们将 BatchTestCase 复制到 TestCase
    stats = await generate_test_cases(
        db=db,
        profile_id=suite.profile_id,
        job_name=f"套件_{suite.name}",
        created_by=user_id,
    )

    # 从刚创建的 BatchTestJob 读取用例，复制到 TestSuite
    from app.models.batch_test import BatchTestCase
    cases_result = await db.execute(
        select(BatchTestCase).where(BatchTestCase.job_id == stats.job_id)
    )
    batch_cases = cases_result.scalars().all()

    for bc in batch_cases:
        tc = TestCase(
            suite_id=suite_id,
            input_text=bc.input_text,
            expected_intent=bc.expected_intent,
            expected_domain=bc.expected_domain,
        )
        db.add(tc)

    # 删除临时 BatchTestJob（级联删除 BatchTestCase）
    from app.models.batch_test import BatchTestJob
    await db.execute(delete(BatchTestJob).where(BatchTestJob.id == stats.job_id))
    await db.flush()

    return len(batch_cases)


async def execute_suite(
    db: AsyncSession,
    redis: aioredis.Redis,
    suite_id: UUID,
    accuracy_threshold: float = 0.95,
    latency_threshold_ms: int = 200,
    user_id: UUID | None = None,
) -> TestReport:
    """执行套件批量测试，生成报告。"""
    suite = await get_suite(db, suite_id)
    if not suite:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="测试套件不存在")

    if not suite.cases:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="套件无测试用例，请先执行生成")

    # 构建 BatchTestCreate
    test_cases = [
        BatchTestCaseInput(
            input_text=c.input_text,
            expected_intent=c.expected_intent,
            expected_domain=c.expected_domain,
        )
        for c in suite.cases
    ]
    batch_create = BatchTestCreate(
        name=f"套件_{suite.name}",
        profile_id=suite.profile_id,
        test_cases=test_cases,
        accuracy_threshold=accuracy_threshold,
        latency_threshold_ms=latency_threshold_ms,
    )

    # 执行批量测试
    job = await create_and_run_batch_test(db, redis, batch_create, user_id)

    # 计算 p95（简化：若 job 无 p95 则用 avg）
    p95 = job.avg_latency_ms
    if job.report and "p95_latency_ms" in job.report:
        p95 = job.report["p95_latency_ms"]

    # 分析报告
    analysis = analyze_report({
        "accuracy": job.accuracy,
        "passed": job.passed_cases,
        "failed": job.failed_cases,
        "avg_latency_ms": job.avg_latency_ms,
        "report": job.report,
    })

    # 创建 TestReport
    report = TestReport(
        suite_id=suite_id,
        total_cases=job.total_cases,
        passed_cases=job.passed_cases,
        failed_cases=job.failed_cases,
        accuracy=job.accuracy or 0,
        avg_latency_ms=job.avg_latency_ms,
        p95_latency_ms=p95,
        is_passed=bool(job.report and job.report.get("overall_pass", False)),
        analysis_report=analysis,
        created_by=user_id,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


async def get_latest_report(db: AsyncSession, suite_id: UUID) -> TestReport | None:
    """获取套件最新测试报告。"""
    result = await db.execute(
        select(TestReport)
        .where(TestReport.suite_id == suite_id)
        .order_by(TestReport.executed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
