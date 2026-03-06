from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import require_permission
from app.schemas.batch_test import BatchTestCreate, BatchTestJobInfo, BatchTestCaseResult
from app.models.batch_test import BatchTestJob, BatchTestCase
from app.services import batch_test_service

router = APIRouter(prefix="/batch-test", tags=["批量测试"])


@router.get("/jobs", response_model=list[BatchTestJobInfo])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    result = await db.execute(select(BatchTestJob).order_by(BatchTestJob.created_at.desc()).limit(50))
    return [BatchTestJobInfo.model_validate(j) for j in result.scalars().all()]


@router.post("/jobs", response_model=BatchTestJobInfo, status_code=201)
async def create_job(
    body: BatchTestCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user=Depends(require_permission("test_debug.write")),
):
    job = await batch_test_service.create_and_run_batch_test(db, redis, body, current_user.id)
    return BatchTestJobInfo.model_validate(job)


@router.get("/jobs/{job_id}", response_model=BatchTestJobInfo)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    result = await db.execute(select(BatchTestJob).where(BatchTestJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="任务不存在")
    return BatchTestJobInfo.model_validate(job)


@router.get("/jobs/{job_id}/cases", response_model=list[BatchTestCaseResult])
async def get_job_cases(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("test_debug.read")),
):
    result = await db.execute(select(BatchTestCase).where(BatchTestCase.job_id == job_id))
    return [BatchTestCaseResult.model_validate(c) for c in result.scalars().all()]
