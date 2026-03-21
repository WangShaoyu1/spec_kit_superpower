"""Dataset management routes (dd-intent-library.md §6.3)."""

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException, paginated_response, success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.models.dataset import EvaluationDataset, TrainingDataset
from app.schemas.intent_library import CreateDatasetRequest, UpdateDatasetRequest
from app.services import data_generation_service, dataset_service

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
