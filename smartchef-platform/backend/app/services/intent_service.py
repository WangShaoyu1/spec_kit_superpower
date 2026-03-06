from uuid import UUID
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.intent import Intent, Slot, TrainingData
from app.schemas.intent import IntentCreate, IntentUpdate, SlotCreate, SlotUpdate, TrainingDataCreate


async def list_intents(
    db: AsyncSession, category: str | None = None, skip: int = 0, limit: int = 50
) -> tuple[list[Intent], int]:
    query = select(Intent).options(selectinload(Intent.slots))
    count_query = select(func.count(Intent.id))

    if category:
        query = query.where(Intent.category == category)
        count_query = count_query.where(Intent.category == category)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Intent.category, Intent.intent_key).offset(skip).limit(limit)
    )
    intents = list(result.scalars().unique().all())

    for intent in intents:
        td_count = (await db.execute(
            select(func.count(TrainingData.id)).where(TrainingData.intent_id == intent.id)
        )).scalar() or 0
        intent._td_count = td_count

    return intents, total


async def get_intent(db: AsyncSession, intent_id: UUID) -> Intent:
    result = await db.execute(
        select(Intent)
        .options(selectinload(Intent.slots), selectinload(Intent.training_data))
        .where(Intent.id == intent_id)
    )
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="意图不存在")
    return intent


async def create_intent(db: AsyncSession, data: IntentCreate, user_id: UUID | None = None) -> Intent:
    existing = await db.execute(select(Intent).where(Intent.intent_key == data.intent_key))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="意图标识已存在")

    intent = Intent(
        intent_key=data.intent_key,
        display_name=data.display_name,
        category=data.category,
        description=data.description,
        created_by=user_id,
    )
    db.add(intent)
    await db.flush()

    for slot_data in data.slots:
        slot = Slot(
            intent_id=intent.id,
            slot_key=slot_data.slot_key,
            display_name=slot_data.display_name,
            entity_type=slot_data.entity_type,
            is_required=slot_data.is_required,
            prompt_text=slot_data.prompt_text,
            constraints=slot_data.constraints,
            sort_order=slot_data.sort_order,
        )
        db.add(slot)

    await db.flush()
    return await get_intent(db, intent.id)


async def update_intent(db: AsyncSession, intent_id: UUID, data: IntentUpdate) -> Intent:
    intent = await get_intent(db, intent_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(intent, key, value)
    await db.flush()
    return await get_intent(db, intent_id)


async def delete_intent(db: AsyncSession, intent_id: UUID) -> None:
    intent = await get_intent(db, intent_id)
    await db.delete(intent)
    await db.flush()


# --- Slot operations ---

async def add_slot(db: AsyncSession, intent_id: UUID, data: SlotCreate) -> Slot:
    await get_intent(db, intent_id)
    slot = Slot(intent_id=intent_id, **data.model_dump())
    db.add(slot)
    await db.flush()
    await db.refresh(slot)
    return slot


async def update_slot(db: AsyncSession, slot_id: UUID, data: SlotUpdate) -> Slot:
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="槽位不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(slot, key, value)
    await db.flush()
    await db.refresh(slot)
    return slot


async def delete_slot(db: AsyncSession, slot_id: UUID) -> None:
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="槽位不存在")
    await db.delete(slot)


# --- Training data operations ---

async def list_training_data(db: AsyncSession, intent_id: UUID) -> list[TrainingData]:
    result = await db.execute(
        select(TrainingData).where(TrainingData.intent_id == intent_id).order_by(TrainingData.created_at)
    )
    return list(result.scalars().all())


async def add_training_data(db: AsyncSession, intent_id: UUID, data: TrainingDataCreate) -> TrainingData:
    await get_intent(db, intent_id)
    td = TrainingData(intent_id=intent_id, **data.model_dump())
    db.add(td)
    await db.flush()
    await db.refresh(td)
    return td


async def batch_add_training_data(
    db: AsyncSession, intent_id: UUID, items: list[TrainingDataCreate]
) -> list[TrainingData]:
    await get_intent(db, intent_id)
    results = []
    for data in items:
        td = TrainingData(intent_id=intent_id, **data.model_dump())
        db.add(td)
        results.append(td)
    await db.flush()
    for td in results:
        await db.refresh(td)
    return results


async def delete_training_data(db: AsyncSession, td_id: UUID) -> None:
    result = await db.execute(select(TrainingData).where(TrainingData.id == td_id))
    td = result.scalar_one_or_none()
    if not td:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练数据不存在")
    await db.delete(td)
