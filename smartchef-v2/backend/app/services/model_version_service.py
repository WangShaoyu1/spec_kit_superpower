"""Model version lifecycle service (dd-intent-library.md §4.2)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.models.dataset import EvaluationDataset
from app.models.evaluation import EvaluationRun
from app.models.intent_library import IntentLibrary
from app.models.model_version import LibraryModelVersion
from app.schemas.intent_library import CreateModelRequest, StartEvaluationRequest, StartTrainingRequest

MAX_NON_ARCHIVED = 5


async def list_model_versions(db: AsyncSession, library_id: UUID) -> list[dict]:
    query = (
        select(LibraryModelVersion)
        .options(selectinload(LibraryModelVersion.train_dataset))
        .where(LibraryModelVersion.library_id == library_id)
        .order_by(LibraryModelVersion.created_at.desc())
    )
    rows = (await db.execute(query)).scalars().all()
    return [_model_to_dict(m) for m in rows]


async def create_model_version(
    db: AsyncSession, library_id: UUID, data: CreateModelRequest, user_id: str,
) -> dict:
    non_archived = (
        await db.execute(
            select(func.count())
            .select_from(LibraryModelVersion)
            .where(LibraryModelVersion.library_id == library_id)
            .where(LibraryModelVersion.status != "archived")
        )
    ).scalar() or 0

    if non_archived >= MAX_NON_ARCHIVED:
        raise BusinessException("E50201", f"非归档模型版本已达上限 ({MAX_NON_ARCHIVED})")

    model = LibraryModelVersion(
        library_id=library_id,
        version_name=data.version_name,
        train_dataset_id=data.train_dataset_id,
        train_config=data.train_config,
        notes=data.notes,
        status="draft",
        created_by=user_id,
    )
    db.add(model)
    await db.flush()
    return _model_to_dict(await _get_model(db, model.id))


async def get_model_version(db: AsyncSession, model_id: UUID) -> dict:
    model = await _get_model(db, model_id)
    return _model_to_dict(model)


async def start_training(
    db: AsyncSession, model_id: UUID, train_opts: StartTrainingRequest | None = None,
) -> dict:
    model = await _get_model(db, model_id)
    if model.status not in ("draft", "trained"):
        raise BusinessException("E50203", f"当前状态 '{model.status}' 不允许启动训练")

    if train_opts is not None:
        extras = train_opts.model_dump(exclude_unset=True)
        if extras:
            merged = dict(model.train_config or {})
            merged.update({k: v for k, v in extras.items() if v is not None})
            model.train_config = merged

    model.status = "training"
    model.progress = 0
    await db.flush()
    # 重新加载含 train_dataset，供响应中的 train_dataset_name / dataset_name（D045）
    return _model_to_dict(await _get_model(db, model_id))


async def complete_training(db: AsyncSession, model_id: UUID, metrics: dict) -> dict:
    model = await _get_model(db, model_id)
    if model.status != "training":
        raise BusinessException("E50203", f"当前状态 '{model.status}' 不允许完成训练")

    model.status = "trained"
    model.metrics = metrics
    model.progress = 100
    model.trained_at = datetime.now(timezone.utc)
    await db.flush()
    return _model_to_dict(await _get_model(db, model_id))


async def start_evaluation(
    db: AsyncSession, model_id: UUID, data: StartEvaluationRequest, user_id: str,
) -> dict:
    model = await _get_model(db, model_id)
    if model.status not in ("trained", "testable", "published"):
        raise BusinessException("E50203", f"当前状态 '{model.status}' 不允许发起评测")

    dataset = await db.get(EvaluationDataset, data.dataset_id)
    if not dataset:
        raise BusinessException("E50501", "评测数据集不存在")

    samples = dataset.samples or []
    if (dataset.sample_count or 0) == 0 and not samples:
        raise BusinessException("E50501", "评估集为空")

    library = await db.get(IntentLibrary, model.library_id)
    run = EvaluationRun(
        library_id=model.library_id,
        model_version_id=model_id,
        dataset_id=data.dataset_id,
        status="pending",
        threshold_intent_f1=data.threshold_intent_f1 or 0.95,
        threshold_slot_f1=data.threshold_slot_f1 or 0.90,
        total_samples=dataset.sample_count or len(samples),
        snapshot={
            "model_status": model.status,
            "model_version_name": model.version_name,
            "dataset_name": dataset.name,
            "dataset_sample_count": dataset.sample_count or len(samples),
            "library_default_threshold": library.default_confidence_threshold if library else 0.7,
        },
        created_by=user_id,
    )
    db.add(run)

    model.status = "evaluating"
    await db.flush()
    await db.refresh(run)
    await db.refresh(model)
    return _eval_to_dict(run)


async def set_testable(db: AsyncSession, model_id: UUID) -> dict:
    model = await _get_model(db, model_id)
    if model.status not in ("trained", "testable", "published"):
        raise BusinessException("E50203", f"当前状态 '{model.status}' 不允许设为可测试")

    await db.execute(
        update(LibraryModelVersion)
        .where(LibraryModelVersion.library_id == model.library_id)
        .where(LibraryModelVersion.is_testable.is_(True))
        .values(is_testable=False)
    )

    model.is_testable = True
    if model.status == "trained":
        model.status = "testable"
    await db.flush()
    return _model_to_dict(await _get_model(db, model_id))


async def publish_model(db: AsyncSession, model_id: UUID, user_id: str) -> dict:
    model = await _get_model(db, model_id)
    if model.status not in ("trained", "testable", "published"):
        raise BusinessException("E50203", f"当前状态 '{model.status}' 不允许发布")

    await db.execute(
        update(LibraryModelVersion)
        .where(LibraryModelVersion.library_id == model.library_id)
        .where(LibraryModelVersion.is_published.is_(True))
        .values(is_published=False)
    )

    model.is_published = True
    model.status = "published"
    model.published_at = datetime.now(timezone.utc)
    model.published_by = user_id
    await db.flush()
    return _model_to_dict(await _get_model(db, model_id))


async def archive_model(db: AsyncSession, model_id: UUID) -> dict:
    model = await _get_model(db, model_id)
    model.status = "archived"
    model.is_testable = False
    model.is_published = False
    await db.flush()
    return _model_to_dict(await _get_model(db, model_id))


async def cancel_training(db: AsyncSession, model_id: UUID) -> dict:
    """将训练中状态标记为失败（训练线程会在下一检查点退出）。"""
    model = await _get_model(db, model_id)
    if model.status != "training":
        raise BusinessException("E50203", "当前不在训练中，无法取消")

    model.status = "failed"
    model.notes = "用户已取消训练"
    model.progress = 0
    await db.flush()
    return _model_to_dict(await _get_model(db, model_id))


async def delete_model_version(db: AsyncSession, model_id: UUID) -> None:
    """删除模型版本记录（草稿 / 失败 / 已归档 / 训练中）。成功态需先归档。"""
    model = await _get_model(db, model_id)
    if model.status in ("trained", "evaluating", "testable", "published"):
        raise BusinessException(
            "E50203",
            "无法删除该状态版本，请先归档后再删除，或仅删除草稿/失败/已归档记录",
        )
    try:
        await db.delete(model)
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise BusinessException(
            "E50203",
            "无法删除：仍存在关联数据（如批量测试引用该模型），请先解除关联",
        ) from None


async def restore_model(db: AsyncSession, model_id: UUID) -> dict:
    model = await _get_model(db, model_id)
    if model.status != "archived":
        raise BusinessException("E50203", "只有归档状态的模型可以恢复")

    non_archived = (
        await db.execute(
            select(func.count())
            .select_from(LibraryModelVersion)
            .where(LibraryModelVersion.library_id == model.library_id)
            .where(LibraryModelVersion.status != "archived")
        )
    ).scalar() or 0

    if non_archived >= MAX_NON_ARCHIVED:
        raise BusinessException("E50201", f"非归档模型版本已达上限 ({MAX_NON_ARCHIVED})")

    model.status = "draft"
    await db.flush()
    return _model_to_dict(await _get_model(db, model_id))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_model(db: AsyncSession, model_id: UUID) -> LibraryModelVersion:
    stmt = (
        select(LibraryModelVersion)
        .options(selectinload(LibraryModelVersion.train_dataset))
        .where(LibraryModelVersion.id == model_id)
    )
    model = (await db.execute(stmt)).scalar_one_or_none()
    if not model:
        raise BusinessException("E50202", "模型版本不存在")
    return model


def _model_to_dict(m: LibraryModelVersion) -> dict:
    train_name = m.train_dataset.name if m.train_dataset is not None else None
    return {
        "id": str(m.id),
        "library_id": str(m.library_id),
        "version_name": m.version_name,
        "status": m.status,
        "train_dataset_id": str(m.train_dataset_id) if m.train_dataset_id else None,
        "train_dataset_name": train_name,
        "dataset_name": train_name,
        "train_config": m.train_config,
        "metrics": m.metrics,
        "artifact_type": m.artifact_type,
        "artifact_uri": m.artifact_uri,
        "package_uri": m.package_uri,
        "notes": m.notes,
        "is_testable": m.is_testable,
        "is_published": m.is_published,
        "progress": m.progress,
        "published_at": m.published_at.isoformat() if m.published_at else None,
        "trained_at": m.trained_at.isoformat() if m.trained_at else None,
        "created_by": str(m.created_by) if m.created_by else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


def _eval_to_dict(r: EvaluationRun) -> dict:
    return {
        "id": str(r.id),
        "library_id": str(r.library_id),
        "model_version_id": str(r.model_version_id),
        "dataset_id": str(r.dataset_id),
        "status": r.status,
        "threshold_intent_f1": r.threshold_intent_f1,
        "threshold_slot_f1": r.threshold_slot_f1,
        "result_summary": r.result_summary,
        "analysis": r.analysis,
        "total_samples": r.total_samples,
        "completed_samples": r.completed_samples,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "created_by": str(r.created_by) if r.created_by else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }
