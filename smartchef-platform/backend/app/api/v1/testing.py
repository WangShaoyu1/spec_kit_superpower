"""测试 API：手动测试 + 批量测试（套件）。"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import require_permission
from app.schemas.test_suite import (
    TestSuiteCreate,
    TestSuiteInfo,
    TestSuiteDetail,
    TestCaseInfo,
    GenerateResponse,
    ExecuteRequest,
    ExecuteResponse,
    TestReportDetail,
)
from app.services.testing import test_suite_service

router = APIRouter(prefix="/testing", tags=["测试"])


# ========== 批量测试套件 ==========

@router.post("/batch/suites", response_model=TestSuiteInfo, status_code=201)
async def create_test_suite(
    body: TestSuiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("test_debug.write")),
):
    """创建测试套件。"""
    suite = await test_suite_service.create_suite(db, body, current_user.id)
    return TestSuiteInfo(
        id=suite.id,
        name=suite.name,
        profile_id=suite.profile_id,
        case_count=0,
        created_at=suite.created_at,
    )


@router.get("/batch/suites", response_model=list[TestSuiteInfo])
async def list_test_suites(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    """列出测试套件。"""
    suites, _ = await test_suite_service.list_suites(db, skip, limit)
    return [
        TestSuiteInfo(
            id=s.id,
            name=s.name,
            profile_id=s.profile_id,
            case_count=getattr(s, "_case_count", 0),
            created_at=s.created_at,
        )
        for s in suites
    ]


@router.get("/batch/suites/{suite_id}", response_model=TestSuiteDetail)
async def get_test_suite(
    suite_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    """获取套件详情（含用例列表）。"""
    suite = await test_suite_service.get_suite(db, suite_id)
    if not suite:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="测试套件不存在")
    return TestSuiteDetail(
        id=suite.id,
        name=suite.name,
        profile_id=suite.profile_id,
        case_count=len(suite.cases),
        cases=[TestCaseInfo.model_validate(c) for c in suite.cases],
        created_at=suite.created_at,
    )


@router.post("/batch/suites/{suite_id}/generate", response_model=GenerateResponse, status_code=201)
async def generate_test_cases_for_suite(
    suite_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("test_debug.write")),
):
    """生成测试用例（调用 case_generator）。"""
    case_count = await test_suite_service.generate_cases_for_suite(db, suite_id, current_user.id)
    return GenerateResponse(
        suite_id=suite_id,
        case_count=case_count,
        message=f"已生成 {case_count} 个测试用例",
    )


@router.post("/batch/suites/{suite_id}/execute", response_model=ExecuteResponse, status_code=202)
async def execute_batch_test(
    suite_id: UUID,
    body: ExecuteRequest | None = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user=Depends(require_permission("test_debug.write")),
):
    """执行批量测试（调用 batch_test）。"""
    req = body or ExecuteRequest()
    report = await test_suite_service.execute_suite(
        db=db,
        redis=redis,
        suite_id=suite_id,
        accuracy_threshold=req.accuracy_threshold,
        latency_threshold_ms=req.latency_threshold_ms,
        user_id=current_user.id,
    )
    return ExecuteResponse(
        report_id=report.id,
        message="批量测试执行完成",
    )


@router.get("/batch/suites/{suite_id}/report", response_model=TestReportDetail)
async def get_test_report(
    suite_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    """获取测试报告（含分析结果）。"""
    report = await test_suite_service.get_latest_report(db, suite_id)
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="该套件暂无测试报告，请先执行批量测试")
    return TestReportDetail.model_validate(report)
