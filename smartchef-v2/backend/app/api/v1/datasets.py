"""Dataset management routes (dd-intent-library.md §6.3)."""

import asyncio
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException, paginated_response, success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.models.dataset import EvaluationDataset, TrainingDataset
from app.schemas.intent_library import CreateDatasetRequest, UpdateDatasetRequest
from app.services import data_generation_service, dataset_service
from app.services import training_generation_job as training_gen_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["datasets"])


# ---------------------------------------------------------------------------
# Training datasets
# ---------------------------------------------------------------------------

@router.get("/intent-libraries/{library_id}/datasets")
async def list_training_datasets(
    request: Request,
    library_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    items, total = await dataset_service.list_training_datasets(
        db, library_id, page=page, page_size=page_size,
    )
    return paginated_response(items, total=total, page=page, page_size=page_size)


@router.post("/intent-libraries/{library_id}/datasets")
@require_capability("intent_library_write")
async def create_training_dataset(
    request: Request,
    library_id: UUID,
    body: CreateDatasetRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await dataset_service.create_training_dataset(db, library_id, body, user.user_id)
    return success_response(data, status_code=201)


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await dataset_service.get_training_dataset(db, dataset_id)
    return success_response(data)


@router.put("/datasets/{dataset_id}")
@require_capability("intent_library_write")
async def update_dataset(
    request: Request,
    dataset_id: UUID,
    body: UpdateDatasetRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await dataset_service.update_training_dataset(db, dataset_id, body)
    return success_response(data)


@router.delete("/datasets/{dataset_id}")
@require_capability("intent_library_delete")
async def delete_dataset(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await dataset_service.delete_training_dataset(db, dataset_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Evaluation datasets
# ---------------------------------------------------------------------------

@router.get("/intent-libraries/{library_id}/eval-datasets")
async def list_evaluation_datasets(
    request: Request,
    library_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    items, total = await dataset_service.list_evaluation_datasets(
        db, library_id, page=page, page_size=page_size,
    )
    return paginated_response(items, total=total, page=page, page_size=page_size)


@router.post("/intent-libraries/{library_id}/eval-datasets")
@require_capability("intent_library_write")
async def create_evaluation_dataset(
    request: Request,
    library_id: UUID,
    body: CreateDatasetRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await dataset_service.create_evaluation_dataset(db, library_id, body, user.user_id)
    return success_response(data, status_code=201)


@router.put("/eval-datasets/{dataset_id}")
@require_capability("intent_library_write")
async def update_evaluation_dataset(
    request: Request,
    dataset_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    data = await dataset_service.update_evaluation_dataset(
        db, dataset_id,
        samples=body.get("samples"),
        sample_count=body.get("sample_count"),
        name=body.get("name"),
        description=body.get("description"),
    )
    return success_response(data)


@router.get("/eval-datasets/{dataset_id}")
async def get_evaluation_dataset(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await dataset_service.get_evaluation_dataset(db, dataset_id)
    return success_response(data)


@router.delete("/eval-datasets/{dataset_id}")
@require_capability("intent_library_delete")
async def delete_evaluation_dataset(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await dataset_service.delete_evaluation_dataset(db, dataset_id)
    return success_response(None, msg="删除成功")


@router.post("/datasets/{dataset_id}/generate-training/jobs")
@require_capability("intent_library_write")
async def start_training_generation_job(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    body: dict | None = Body(default=None),
):
    """异步生成相似问：立即返回 job_id，客户端轮询 GET .../jobs/{job_id} 查看进度。

    使用 asyncio.create_task 调度后台协程。直接 return JSONResponse 时 Starlette 的
    BackgroundTasks 可能不会挂到响应上，导致任务从未执行、状态一直为 queued。
    """
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "训练数据集不存在")
    merged = {**(body or {}), "dataset_id": str(dataset_id)}
    job_id = str(uuid4())
    await training_gen_job.save_job_state(
        job_id,
        {
            "job_id": job_id,
            "dataset_id": str(dataset_id),
            "library_id": str(ds.library_id),
            "status": "queued",
            "intent_index": 0,
            "intent_total": 0,
            "generated_count": 0,
            "errors": [],
        },
    )
    # 先提交当前请求的事务，再启动后台任务，避免任务内读库看不到已提交数据
    await db.commit()

    task = asyncio.create_task(
        training_gen_job.run_training_generation_job(job_id, ds.library_id, merged)
    )

    def _log_task_result(t: asyncio.Task) -> None:
        try:
            exc = t.exception()
            if exc is not None:
                logger.error("training job %s task failed: %s", job_id, exc)
        except asyncio.CancelledError:
            pass

    task.add_done_callback(_log_task_result)

    return JSONResponse(
        status_code=202,
        content={
            "code": "000000",
            "data": {
                "job_id": job_id,
                "poll_interval_sec": 6,
                "status_path": f"/api/v1/datasets/{dataset_id}/generate-training/jobs/{job_id}",
            },
            "msg": "accepted",
        },
    )


@router.get("/datasets/{dataset_id}/generate-training/jobs/{job_id}")
async def get_training_generation_job(
    request: Request,
    dataset_id: UUID,
    job_id: str,
):
    await get_current_user_from_token(request)
    st = await training_gen_job.load_job_state(job_id)
    if not st:
        raise BusinessException("E50604", "任务不存在或已过期", http_status=404)
    if st.get("dataset_id") != str(dataset_id):
        raise BusinessException("E50604", "任务不存在", http_status=404)
    return success_response(st)


@router.post("/datasets/{dataset_id}/generate-training")
@require_capability("intent_library_write")
async def generate_training_data(
    request: Request,
    dataset_id: UUID,
    body: dict | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "训练数据集不存在")
    merged = {**(body or {}), "dataset_id": str(dataset_id)}
    result = await data_generation_service.generate_training_data(db, ds.library_id, merged)
    return success_response(result)


@router.post("/intent-libraries/{library_id}/eval-datasets/{dataset_id}/generate")
@require_capability("intent_library_write")
async def generate_evaluation_data(
    request: Request,
    library_id: UUID,
    dataset_id: UUID,
    body: dict | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    ed = await db.get(EvaluationDataset, dataset_id)
    if not ed:
        raise BusinessException("E50501", "评测数据集不存在")
    if ed.library_id != library_id:
        raise BusinessException("E50502", "评测数据集不属于该意图库")
    merged = {**(body or {}), "dataset_id": str(dataset_id)}
    result = await data_generation_service.generate_evaluation_data(db, library_id, merged)
    return success_response(result)


@router.post("/datasets/{dataset_id}/generate-evaluation")
@require_capability("intent_library_write")
async def generate_evaluation_data_v2(
    request: Request,
    dataset_id: UUID,
    body: dict | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    ed = await db.get(EvaluationDataset, dataset_id)
    if not ed:
        raise BusinessException("E50501", "评测数据集不存在")
    merged = {**(body or {}), "dataset_id": str(dataset_id)}
    result = await data_generation_service.generate_evaluation_data(db, ed.library_id, merged)
    return success_response(result)
