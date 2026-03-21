"""Batch Test API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.api_response import paginated_response, success_response
from app.core.database import get_db
from app.core.security import require_capability
from app.models.batch_test import TestRun, TestRunAnalysis
from app.schemas.batch_test import (
    BatchTestCreate,
    BatchTestOut,
    GenerateCasesRequest,
    TestCaseCreate,
    TestCaseImportRequest,
    TestCaseOut,
    TestCaseUpdate,
    TestRunAnalysisOut,
    TestRunOut,
)
from app.services.testing import analyzer, batch_executor, batch_service, case_service

router = APIRouter(prefix="/batch-tests", tags=["batch-tests"])


# ---------------------------------------------------------------------------
# Batch CRUD
# ---------------------------------------------------------------------------


@router.get("")
@require_capability("batch_test_read")
async def list_batch_tests(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, total = await batch_service.list_batches(
        db, page=page, page_size=page_size, search=search, status=status,
    )
    return paginated_response(items, total=total, page=page, page_size=page_size)


@router.get("/stats")
@require_capability("batch_test_read")
async def get_batch_stats(request: Request, db: AsyncSession = Depends(get_db)):
    stats = await batch_service.get_stats(db)
    return success_response(stats)


@router.post("")
@require_capability("batch_test_write")
async def create_batch_test(
    request: Request,
    body: BatchTestCreate,
    db: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "current_user", None)
    batch = await batch_service.create_batch(db, body, user_id=user.user_id if user else None)
    return success_response(
        BatchTestOut.model_validate(batch).model_dump(mode="json"),
        status_code=201,
    )


@router.get("/{batch_id}")
@require_capability("batch_test_read")
async def get_batch_test(
    request: Request,
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    batch = await batch_service.get_batch(db, batch_id)
    out = BatchTestOut.model_validate(batch).model_dump(mode="json")
    out["profile_name"] = batch.profile.name if batch.profile else None
    return success_response(out)


@router.delete("/{batch_id}")
@require_capability("batch_test_write")
async def delete_batch_test(
    request: Request,
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await batch_service.delete_batch(db, batch_id)
    return success_response(msg="删除成功")


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


@router.get("/{batch_id}/cases")
@require_capability("batch_test_read")
async def list_cases(
    request: Request,
    batch_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await case_service.list_cases(db, batch_id, page=page, page_size=page_size)
    return paginated_response(items, total=total, page=page, page_size=page_size)


@router.post("/{batch_id}/cases")
@require_capability("batch_test_write")
async def add_case(
    request: Request,
    batch_id: UUID,
    body: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    await batch_service.get_batch(db, batch_id)
    case = await case_service.create_case(db, batch_id, body)
    batch = await batch_service.get_batch(db, batch_id)
    await batch_service.refresh_case_count(db, batch)
    return success_response(
        TestCaseOut.model_validate(case).model_dump(mode="json"),
        status_code=201,
    )


@router.put("/{batch_id}/cases/{case_id}")
@require_capability("batch_test_write")
async def update_case(
    request: Request,
    batch_id: UUID,
    case_id: UUID,
    body: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    case = await case_service.update_case(db, case_id, body)
    return success_response(TestCaseOut.model_validate(case).model_dump(mode="json"))


@router.delete("/{batch_id}/cases/{case_id}")
@require_capability("batch_test_write")
async def delete_case(
    request: Request,
    batch_id: UUID,
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    ret_batch_id = await case_service.delete_case(db, case_id)
    batch = await batch_service.get_batch(db, ret_batch_id)
    await batch_service.refresh_case_count(db, batch)
    return success_response(msg="删除成功")


@router.post("/{batch_id}/import-cases")
@require_capability("batch_test_write")
async def import_cases(
    request: Request,
    batch_id: UUID,
    body: TestCaseImportRequest,
    db: AsyncSession = Depends(get_db),
):
    await batch_service.get_batch(db, batch_id)
    count = await case_service.create_cases_bulk(db, batch_id, body.cases)
    batch = await batch_service.get_batch(db, batch_id)
    await batch_service.refresh_case_count(db, batch)
    return success_response({"imported": count}, status_code=201)


@router.get("/{batch_id}/export-cases")
@require_capability("batch_test_read")
async def export_cases(
    request: Request,
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await case_service.export_cases(db, batch_id)
    return success_response(data)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


@router.post("/{batch_id}/execute")
@require_capability("batch_test_execute")
async def execute_batch(
    request: Request,
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    batch = await batch_executor.execute_batch(db, batch_id)
    return success_response(BatchTestOut.model_validate(batch).model_dump(mode="json"))


@router.get("/{batch_id}/runs")
@require_capability("batch_test_read")
async def list_runs(
    request: Request,
    batch_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    count_q = select(func.count()).select_from(TestRun).where(TestRun.batch_id == batch_id)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(TestRun)
        .options(joinedload(TestRun.case))
        .where(TestRun.batch_id == batch_id)
        .order_by(TestRun.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    runs = result.unique().scalars().all()

    items = []
    for r in runs:
        out = TestRunOut.model_validate(r).model_dump(mode="json")
        if r.case:
            out["input_text"] = r.case.input_text
            out["expected_intent"] = r.case.expected_intent
        items.append(out)

    return paginated_response(items, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


@router.get("/{batch_id}/analysis")
@require_capability("batch_test_read")
async def get_analysis(
    request: Request,
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestRunAnalysis)
        .where(TestRunAnalysis.batch_id == batch_id)
        .order_by(TestRunAnalysis.created_at.desc())
        .limit(1)
    )
    existing = result.scalars().first()
    if existing:
        return success_response(TestRunAnalysisOut.model_validate(existing).model_dump(mode="json"))
    return success_response(None)


@router.post("/{batch_id}/analyze")
@require_capability("batch_test_read")
async def trigger_analysis(
    request: Request,
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    analysis = await analyzer.generate_analysis(db, batch_id)
    return success_response(TestRunAnalysisOut.model_validate(analysis).model_dump(mode="json"))


# ---------------------------------------------------------------------------
# LLM Case Generation (placeholder)
# ---------------------------------------------------------------------------


@router.post("/{batch_id}/generate-cases")
@require_capability("batch_test_write")
async def generate_cases(
    request: Request,
    batch_id: UUID,
    body: GenerateCasesRequest,
    db: AsyncSession = Depends(get_db),
):
    await batch_service.get_batch(db, batch_id)
    n = await case_service.append_generated_cases(db, batch_id, body)
    batch = await batch_service.get_batch(db, batch_id)
    await batch_service.refresh_case_count(db, batch)
    return success_response({"generated": n}, msg=f"已生成 {n} 条用例")
