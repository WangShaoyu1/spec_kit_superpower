"""Intent / Slot / Entity / SimilarQuestion / NegativeExample CRUD service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.dataset import TrainingDataset
from app.models.intent import Intent, NegativeExample, SimilarQuestion
from app.models.slot import Slot, SlotEntity


# ---------------------------------------------------------------------------
# Intent CRUD
# ---------------------------------------------------------------------------

async def list_intents(db: AsyncSession, dataset_id: UUID) -> list[dict]:
    query = (
        select(Intent)
        .where(Intent.dataset_id == dataset_id)
        .order_by(Intent.sort_order, Intent.created_at)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_intent_to_dict(i) for i in rows]


async def create_intent(db: AsyncSession, dataset_id: UUID, data) -> dict:
    await _check_dataset(db, dataset_id)

    existing = await db.execute(
        select(Intent)
        .where(Intent.dataset_id == dataset_id)
        .where(Intent.intent_key == data.intent_key)
    )
    if existing.scalar():
        raise BusinessException("E50301", f"意图 key '{data.intent_key}' 已存在")

    intent = Intent(
        dataset_id=dataset_id,
        intent_key=data.intent_key,
        name_zh=data.name_zh,
        description=data.description,
        slot_keys=data.slot_keys,
        follow_up_enabled=data.follow_up_enabled,
        follow_up_prompt=data.follow_up_prompt,
        hit_responses=data.hit_responses,
        miss_response=data.miss_response,
        sort_order=data.sort_order,
    )
    db.add(intent)
    await db.flush()
    await _update_dataset_counts(db, dataset_id)
    return _intent_to_dict(intent)


async def get_intent(db: AsyncSession, intent_id: UUID) -> dict:
    intent = await db.get(Intent, intent_id)
    if not intent:
        raise BusinessException("E50302", "意图不存在")
    return _intent_to_dict(intent)


async def update_intent(db: AsyncSession, intent_id: UUID, data) -> dict:
    intent = await db.get(Intent, intent_id)
    if not intent:
        raise BusinessException("E50302", "意图不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(intent, key, val)

    await db.flush()
    return _intent_to_dict(intent)


async def delete_intent(db: AsyncSession, intent_id: UUID) -> None:
    intent = await db.get(Intent, intent_id)
    if not intent:
        raise BusinessException("E50302", "意图不存在")

    dataset_id = intent.dataset_id
    await db.delete(intent)
    await db.flush()
    await _update_dataset_counts(db, dataset_id)


# ---------------------------------------------------------------------------
# Slot CRUD
# ---------------------------------------------------------------------------

async def list_slots(db: AsyncSession, dataset_id: UUID) -> list[dict]:
    query = (
        select(Slot)
        .where(Slot.dataset_id == dataset_id)
        .order_by(Slot.sort_order, Slot.created_at)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_slot_to_dict(s) for s in rows]


async def create_slot(db: AsyncSession, dataset_id: UUID, data) -> dict:
    await _check_dataset(db, dataset_id)

    existing = await db.execute(
        select(Slot).where(Slot.dataset_id == dataset_id).where(Slot.slot_key == data.slot_key)
    )
    if existing.scalar():
        raise BusinessException("E50401", f"槽位 key '{data.slot_key}' 已存在")

    slot = Slot(
        dataset_id=dataset_id,
        slot_key=data.slot_key,
        name_zh=data.name_zh,
        description=data.description,
        slot_type=data.slot_type,
        is_required=data.is_required,
        prompt_text=data.prompt_text,
        sort_order=data.sort_order,
    )
    db.add(slot)
    await db.flush()
    return _slot_to_dict(slot)


async def get_slot(db: AsyncSession, slot_id: UUID) -> dict:
    slot = await db.get(Slot, slot_id)
    if not slot:
        raise BusinessException("E50402", "槽位不存在")
    return _slot_to_dict(slot)


async def update_slot(db: AsyncSession, slot_id: UUID, data) -> dict:
    slot = await db.get(Slot, slot_id)
    if not slot:
        raise BusinessException("E50402", "槽位不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(slot, key, val)

    await db.flush()
    return _slot_to_dict(slot)


async def delete_slot(db: AsyncSession, slot_id: UUID) -> None:
    slot = await db.get(Slot, slot_id)
    if not slot:
        raise BusinessException("E50402", "槽位不存在")

    await db.delete(slot)
    await db.flush()


# ---------------------------------------------------------------------------
# SlotEntity CRUD
# ---------------------------------------------------------------------------

async def list_entities(db: AsyncSession, slot_id: UUID) -> list[dict]:
    query = (
        select(SlotEntity)
        .where(SlotEntity.slot_id == slot_id)
        .order_by(SlotEntity.sort_order)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_entity_to_dict(e) for e in rows]


async def create_entity(db: AsyncSession, slot_id: UUID, data) -> dict:
    slot = await db.get(Slot, slot_id)
    if not slot:
        raise BusinessException("E50402", "槽位不存在")

    entity = SlotEntity(
        slot_id=slot_id,
        value=data.value,
        synonyms=data.synonyms,
        sort_order=data.sort_order,
    )
    db.add(entity)
    await db.flush()
    return _entity_to_dict(entity)


async def update_entity(db: AsyncSession, entity_id: UUID, data) -> dict:
    entity = await db.get(SlotEntity, entity_id)
    if not entity:
        raise BusinessException("E50403", "实体值不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(entity, key, val)

    await db.flush()
    return _entity_to_dict(entity)


async def delete_entity(db: AsyncSession, entity_id: UUID) -> None:
    entity = await db.get(SlotEntity, entity_id)
    if not entity:
        raise BusinessException("E50403", "实体值不存在")

    await db.delete(entity)
    await db.flush()


# ---------------------------------------------------------------------------
# SimilarQuestion CRUD
# ---------------------------------------------------------------------------

async def list_similar_questions(db: AsyncSession, intent_id: UUID) -> list[dict]:
    query = (
        select(SimilarQuestion)
        .where(SimilarQuestion.intent_id == intent_id)
        .order_by(SimilarQuestion.sort_order)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_sq_to_dict(sq) for sq in rows]


async def create_similar_question(db: AsyncSession, intent_id: UUID, data) -> dict:
    intent = await db.get(Intent, intent_id)
    if not intent:
        raise BusinessException("E50302", "意图不存在")

    sq = SimilarQuestion(
        intent_id=intent_id,
        text=data.text,
        slot_annotations=data.slot_annotations,
        source=data.source,
        sort_order=data.sort_order,
    )
    db.add(sq)
    await db.flush()
    await _update_dataset_counts(db, intent.dataset_id)
    return _sq_to_dict(sq)


async def update_similar_question(db: AsyncSession, sq_id: UUID, data) -> dict:
    sq = await db.get(SimilarQuestion, sq_id)
    if not sq:
        raise BusinessException("E50303", "相似问不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(sq, key, val)

    await db.flush()
    return _sq_to_dict(sq)


async def delete_similar_question(db: AsyncSession, sq_id: UUID) -> None:
    sq = await db.get(SimilarQuestion, sq_id)
    if not sq:
        raise BusinessException("E50303", "相似问不存在")

    intent = await db.get(Intent, sq.intent_id)
    await db.delete(sq)
    await db.flush()
    if intent:
        await _update_dataset_counts(db, intent.dataset_id)


# ---------------------------------------------------------------------------
# NegativeExample CRUD
# ---------------------------------------------------------------------------

async def list_negative_examples(db: AsyncSession, intent_id: UUID) -> list[dict]:
    query = (
        select(NegativeExample)
        .where(NegativeExample.intent_id == intent_id)
    )
    rows = (await db.execute(query)).scalars().all()
    return [_ne_to_dict(ne) for ne in rows]


async def create_negative_example(db: AsyncSession, intent_id: UUID, data) -> dict:
    intent = await db.get(Intent, intent_id)
    if not intent:
        raise BusinessException("E50302", "意图不存在")

    ne = NegativeExample(
        intent_id=intent_id,
        text=data.text,
        source=data.source,
    )
    db.add(ne)
    await db.flush()
    await _update_dataset_counts(db, intent.dataset_id)
    return _ne_to_dict(ne)


async def delete_negative_example(db: AsyncSession, ne_id: UUID) -> None:
    ne = await db.get(NegativeExample, ne_id)
    if not ne:
        raise BusinessException("E50304", "反例不存在")

    intent = await db.get(Intent, ne.intent_id)
    await db.delete(ne)
    await db.flush()
    if intent:
        await _update_dataset_counts(db, intent.dataset_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _check_dataset(db: AsyncSession, dataset_id: UUID) -> TrainingDataset:
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        raise BusinessException("E50501", "训练数据集不存在")
    return ds


async def _update_dataset_counts(db: AsyncSession, dataset_id: UUID) -> None:
    """Recalculate intent_count and sample_count on the parent dataset."""
    ds = await db.get(TrainingDataset, dataset_id)
    if not ds:
        return

    intent_count = (
        await db.execute(
            select(func.count()).select_from(Intent).where(Intent.dataset_id == dataset_id)
        )
    ).scalar() or 0

    sample_count = (
        await db.execute(
            select(func.count())
            .select_from(SimilarQuestion)
            .join(Intent, SimilarQuestion.intent_id == Intent.id)
            .where(Intent.dataset_id == dataset_id)
        )
    ).scalar() or 0

    neg_count = (
        await db.execute(
            select(func.count())
            .select_from(NegativeExample)
            .join(Intent, NegativeExample.intent_id == Intent.id)
            .where(Intent.dataset_id == dataset_id)
        )
    ).scalar() or 0

    ds.intent_count = intent_count
    ds.sample_count = sample_count + neg_count
    await db.flush()


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _intent_to_dict(i: Intent) -> dict:
    return {
        "id": str(i.id),
        "dataset_id": str(i.dataset_id),
        "intent_key": i.intent_key,
        "name_zh": i.name_zh,
        "description": i.description,
        "slot_keys": i.slot_keys,
        "follow_up_enabled": i.follow_up_enabled,
        "follow_up_prompt": i.follow_up_prompt,
        "hit_responses": i.hit_responses,
        "miss_response": i.miss_response,
        "sort_order": i.sort_order,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "updated_at": i.updated_at.isoformat() if i.updated_at else None,
    }


def _slot_to_dict(s: Slot) -> dict:
    return {
        "id": str(s.id),
        "dataset_id": str(s.dataset_id),
        "slot_key": s.slot_key,
        "name_zh": s.name_zh,
        "description": s.description,
        "slot_type": s.slot_type,
        "is_required": s.is_required,
        "prompt_text": s.prompt_text,
        "sort_order": s.sort_order,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _entity_to_dict(e: SlotEntity) -> dict:
    return {
        "id": str(e.id),
        "slot_id": str(e.slot_id),
        "value": e.value,
        "synonyms": e.synonyms,
        "sort_order": e.sort_order,
    }


def _sq_to_dict(sq: SimilarQuestion) -> dict:
    return {
        "id": str(sq.id),
        "intent_id": str(sq.intent_id),
        "text": sq.text,
        "slot_annotations": sq.slot_annotations,
        "source": sq.source,
        "sort_order": sq.sort_order,
    }


def _ne_to_dict(ne: NegativeExample) -> dict:
    return {
        "id": str(ne.id),
        "intent_id": str(ne.intent_id),
        "text": ne.text,
        "source": ne.source,
    }
