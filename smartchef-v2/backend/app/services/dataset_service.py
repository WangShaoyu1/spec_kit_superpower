"""Dataset CRUD service for training and evaluation datasets (dd-intent-library.md §4.3)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.dataset import EvaluationDataset, TrainingDataset
from app.models.evaluation import EvaluationRun
from app.models.model_version import LibraryModelVersion
from app.schemas.intent_library import CreateDatasetRequest, UpdateDatasetRequest


# ---------------------------------------------------------------------------
# Training datasets
# ---------------------------------------------------------------------------

async def list_training_datasets(
    db: AsyncSession, library_id: UUID, page: int = 1, page_size: int = 20,
) -> tuple[list[dict], int]:
    count_q = (
        select(func.count())
        .select_from(TrainingDataset)
        .where(TrainingDataset.library_id == library_id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(TrainingDataset)
        .where(TrainingDataset.library_id == library_id)
        .order_by(TrainingDataset.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_td_to_dict(ds) for ds in rows], total


async def create_training_dataset(
    db: AsyncSession, library_id: UUID, data: CreateDatasetRequest, user_id: str,
) -> dict:
    ds = TrainingDataset(
        library_id=library_id,
        name=data.name,
        description=data.description,
        source_type=data.source_type,
        config=data.config,
        created_by=user_id,
    )
    db.add(ds)
    await db.flush()
    return _td_to_dict(ds)


async def get_training_dataset(db: AsyncSession, dataset_id: UUID) -> dict:
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "训练数据集不存在")
    return _td_to_dict(ds)


async def update_training_dataset(
    db: AsyncSession, dataset_id: UUID, data: UpdateDatasetRequest,
) -> dict:
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "训练数据集不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(ds, key, val)

    await db.flush()
    return _td_to_dict(ds)


async def delete_training_dataset(db: AsyncSession, dataset_id: UUID) -> None:
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "训练数据集不存在")

    bound = (
        await db.execute(
            select(func.count())
            .select_from(LibraryModelVersion)
            .where(LibraryModelVersion.train_dataset_id == dataset_id)
        )
    ).scalar() or 0

    if bound > 0:
        raise BusinessException("E50520", "数据集已绑定模型版本，无法删除")

    await db.delete(ds)
    await db.flush()


# ---------------------------------------------------------------------------
# Evaluation datasets
# ---------------------------------------------------------------------------

async def list_evaluation_datasets(
    db: AsyncSession, library_id: UUID, page: int = 1, page_size: int = 20,
) -> tuple[list[dict], int]:
    count_q = (
        select(func.count())
        .select_from(EvaluationDataset)
        .where(EvaluationDataset.library_id == library_id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(EvaluationDataset)
        .where(EvaluationDataset.library_id == library_id)
        .order_by(EvaluationDataset.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_ed_to_dict(ds) for ds in rows], total


async def create_evaluation_dataset(
    db: AsyncSession, library_id: UUID, data: CreateDatasetRequest, user_id: str,
) -> dict:
    ds = EvaluationDataset(
        library_id=library_id,
        name=data.name,
        description=data.description,
        source_type=data.source_type,
        config=data.config,
        created_by=user_id,
    )
    db.add(ds)
    await db.flush()
    return _ed_to_dict(ds)


async def update_evaluation_dataset(
    db: AsyncSession, dataset_id: UUID, *, samples: list | None = None,
    sample_count: int | None = None, name: str | None = None,
    description: str | None = None,
) -> dict:
    ds = await db.get(EvaluationDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "评测数据集不存在")
    if samples is not None:
        ds.samples = samples
        ds.sample_count = len(samples)
    if sample_count is not None and samples is None:
        ds.sample_count = sample_count
    if name is not None:
        ds.name = name
    if description is not None:
        ds.description = description
    await db.flush()
    await db.refresh(ds)
    return _ed_to_dict(ds)


async def get_evaluation_dataset(db: AsyncSession, dataset_id: UUID) -> dict:
    ds = await db.get(EvaluationDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "评测数据集不存在")
    return _ed_to_dict(ds)


async def delete_evaluation_dataset(db: AsyncSession, dataset_id: UUID) -> None:
    ds = await db.get(EvaluationDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "评测数据集不存在")

    run_count = (
        await db.execute(
            select(func.count())
            .select_from(EvaluationRun)
            .where(EvaluationRun.dataset_id == dataset_id)
        )
    ).scalar() or 0

    if run_count > 0:
        raise BusinessException("E50520", "评测数据集已关联评测记录，无法删除")

    await db.delete(ds)
    await db.flush()


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _td_to_dict(ds: TrainingDataset) -> dict:
    return {
        "id": str(ds.id),
        "library_id": str(ds.library_id),
        "name": ds.name,
        "description": ds.description,
        "source_type": ds.source_type,
        "schema_version": ds.schema_version,
        "sample_count": ds.sample_count,
        "intent_count": ds.intent_count,
        "config": ds.config,
        "file_uri": ds.file_uri,
        "is_active": ds.is_active,
        "created_by": str(ds.created_by) if ds.created_by else None,
        "created_at": ds.created_at.isoformat() if ds.created_at else None,
        "updated_at": ds.updated_at.isoformat() if ds.updated_at else None,
    }


def _ed_to_dict(ds: EvaluationDataset) -> dict:
    return {
        "id": str(ds.id),
        "library_id": str(ds.library_id),
        "name": ds.name,
        "description": ds.description,
        "source_type": ds.source_type,
        "schema_version": ds.schema_version,
        "sample_count": ds.sample_count,
        "config": ds.config,
        "file_uri": ds.file_uri,
        "is_active": ds.is_active,
        "created_by": str(ds.created_by) if ds.created_by else None,
        "created_at": ds.created_at.isoformat() if ds.created_at else None,
        "updated_at": ds.updated_at.isoformat() if ds.updated_at else None,
    }
