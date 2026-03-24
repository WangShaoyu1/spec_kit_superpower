"""Batch Test CRUD and status management."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.api_response import BusinessException
from app.models.batch_test import BatchTest, TestCase
from app.schemas.batch_test import BatchTestCreate, BatchTestOut, BatchTestStats

_VALID_TRANSITIONS = {
    "draft": {"ready", "draft"},
    "ready": {"running", "draft"},
    "running": {"completed", "failed"},
    "completed": {"draft"},
    "failed": {"draft"},
}


async def list_batches(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    status: str | None = None,
) -> tuple[list[dict], int]:
    query = select(BatchTest).options(joinedload(BatchTest.profile))
    count_query = select(func.count()).select_from(BatchTest)

    if search:
        query = query.where(BatchTest.name.ilike(f"%{search}%"))
        count_query = count_query.where(BatchTest.name.ilike(f"%{search}%"))
    if status:
        query = query.where(BatchTest.status == status)
        count_query = count_query.where(BatchTest.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(BatchTest.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    batches = result.unique().scalars().all()

    items = []
    for b in batches:
        out = BatchTestOut.model_validate(b).model_dump()
        out["profile_name"] = b.profile.name if b.profile else None
        items.append(out)

    return items, total


async def get_stats(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).select_from(BatchTest))).scalar() or 0
    running = (
        await db.execute(
            select(func.count()).select_from(BatchTest).where(BatchTest.status == "running")
        )
    ).scalar() or 0
    completed = (
        await db.execute(
            select(func.count()).select_from(BatchTest).where(BatchTest.status == "completed")
        )
    ).scalar() or 0
    avg_acc = (
        await db.execute(
            select(func.avg(BatchTest.accuracy)).where(BatchTest.accuracy.isnot(None))
        )
    ).scalar()

    return BatchTestStats(
        total=total,
        running=running,
        completed=completed,
        avg_accuracy=round(avg_acc, 4) if avg_acc is not None else None,
    ).model_dump()


async def create_batch(db: AsyncSession, data: BatchTestCreate, user_id: str | None = None) -> BatchTest:
    if data.model_id is None and data.profile_id is None:
        raise BusinessException("E50104", "批量测试必须绑定 model_id 或 profile_id")
    if data.model_id is not None and data.profile_id is not None:
        raise BusinessException("E50105", "批量测试不能同时绑定 model_id 和 profile_id")

    batch = BatchTest(
        id=uuid.uuid4(),
        name=data.name,
        description=data.description,
        profile_id=data.profile_id,
        model_id=data.model_id,
        accuracy_threshold=data.accuracy_threshold,
        latency_threshold_ms=data.latency_threshold_ms,
        created_by=uuid.UUID(user_id) if user_id else None,
    )
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return batch


async def get_batch(db: AsyncSession, batch_id: uuid.UUID) -> BatchTest:
    result = await db.execute(
        select(BatchTest).options(joinedload(BatchTest.profile)).where(BatchTest.id == batch_id)
    )
    batch = result.unique().scalars().first()
    if not batch:
        raise BusinessException("E50101", "批量测试不存在", http_status=404)
    return batch


async def delete_batch(db: AsyncSession, batch_id: uuid.UUID) -> None:
    batch = await get_batch(db, batch_id)
    await db.delete(batch)
    await db.flush()


async def transition_status(db: AsyncSession, batch: BatchTest, new_status: str) -> BatchTest:
    allowed = _VALID_TRANSITIONS.get(batch.status, set())
    if new_status not in allowed:
        raise BusinessException(
            "E50102",
            f"状态不允许从 {batch.status} 转换到 {new_status}",
        )
    batch.status = new_status
    await db.flush()
    return batch


async def refresh_case_count(db: AsyncSession, batch: BatchTest) -> BatchTest:
    count = (
        await db.execute(
            select(func.count()).select_from(TestCase).where(TestCase.batch_id == batch.id)
        )
    ).scalar() or 0
    batch.total_cases = count

    if count > 0 and batch.status == "draft":
        batch.status = "ready"
    elif count == 0 and batch.status == "ready":
        batch.status = "draft"

    await db.flush()
    return batch
