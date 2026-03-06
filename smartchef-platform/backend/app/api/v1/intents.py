from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.schemas.intent import (
    IntentCreate, IntentInfo, IntentUpdate, IntentListResponse,
    SlotCreate, SlotInfo, SlotUpdate,
    TrainingDataCreate, TrainingDataInfo,
)
from app.services import intent_service

router = APIRouter(prefix="/intents", tags=["意图配置管理"])


@router.get("", response_model=IntentListResponse)
async def list_intents(
    category: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.read")),
):
    intents, total = await intent_service.list_intents(db, category, skip, limit)
    items = []
    for intent in intents:
        info = IntentInfo(
            id=intent.id,
            intent_key=intent.intent_key,
            display_name=intent.display_name,
            category=intent.category,
            description=intent.description,
            is_active=intent.is_active,
            slots=[SlotInfo.model_validate(s) for s in intent.slots],
            training_data_count=getattr(intent, "_td_count", 0),
            created_at=intent.created_at,
            updated_at=intent.updated_at,
        )
        items.append(info)
    return IntentListResponse(items=items, total=total)


@router.post("", response_model=IntentInfo, status_code=201)
async def create_intent(
    body: IntentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("intent_management.write")),
):
    intent = await intent_service.create_intent(db, body, current_user.id)
    return IntentInfo(
        id=intent.id,
        intent_key=intent.intent_key,
        display_name=intent.display_name,
        category=intent.category,
        description=intent.description,
        is_active=intent.is_active,
        slots=[SlotInfo.model_validate(s) for s in intent.slots],
        training_data_count=len(intent.training_data),
        created_at=intent.created_at,
        updated_at=intent.updated_at,
    )


@router.get("/{intent_id}", response_model=IntentInfo)
async def get_intent(
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.read")),
):
    intent = await intent_service.get_intent(db, intent_id)
    return IntentInfo(
        id=intent.id,
        intent_key=intent.intent_key,
        display_name=intent.display_name,
        category=intent.category,
        description=intent.description,
        is_active=intent.is_active,
        slots=[SlotInfo.model_validate(s) for s in intent.slots],
        training_data_count=len(intent.training_data),
        created_at=intent.created_at,
        updated_at=intent.updated_at,
    )


@router.patch("/{intent_id}", response_model=IntentInfo)
async def update_intent(
    intent_id: UUID,
    body: IntentUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.write")),
):
    intent = await intent_service.update_intent(db, intent_id, body)
    return IntentInfo(
        id=intent.id,
        intent_key=intent.intent_key,
        display_name=intent.display_name,
        category=intent.category,
        description=intent.description,
        is_active=intent.is_active,
        slots=[SlotInfo.model_validate(s) for s in intent.slots],
        training_data_count=len(intent.training_data),
        created_at=intent.created_at,
        updated_at=intent.updated_at,
    )


@router.delete("/{intent_id}", status_code=204)
async def delete_intent(
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.delete")),
):
    await intent_service.delete_intent(db, intent_id)


# --- Slot endpoints ---

@router.post("/{intent_id}/slots", response_model=SlotInfo, status_code=201)
async def add_slot(
    intent_id: UUID,
    body: SlotCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.write")),
):
    slot = await intent_service.add_slot(db, intent_id, body)
    return SlotInfo.model_validate(slot)


@router.patch("/slots/{slot_id}", response_model=SlotInfo)
async def update_slot(
    slot_id: UUID,
    body: SlotUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.write")),
):
    slot = await intent_service.update_slot(db, slot_id, body)
    return SlotInfo.model_validate(slot)


@router.delete("/slots/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.delete")),
):
    await intent_service.delete_slot(db, slot_id)


# --- Training data endpoints ---

@router.get("/{intent_id}/training-data", response_model=list[TrainingDataInfo])
async def list_training_data(
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.read")),
):
    items = await intent_service.list_training_data(db, intent_id)
    return [TrainingDataInfo.model_validate(td) for td in items]


@router.post("/{intent_id}/training-data", response_model=TrainingDataInfo, status_code=201)
async def add_training_data(
    intent_id: UUID,
    body: TrainingDataCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.write")),
):
    td = await intent_service.add_training_data(db, intent_id, body)
    return TrainingDataInfo.model_validate(td)


@router.post("/{intent_id}/training-data/batch", response_model=list[TrainingDataInfo], status_code=201)
async def batch_add_training_data(
    intent_id: UUID,
    body: list[TrainingDataCreate],
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.write")),
):
    items = await intent_service.batch_add_training_data(db, intent_id, body)
    return [TrainingDataInfo.model_validate(td) for td in items]


@router.delete("/training-data/{td_id}", status_code=204)
async def delete_training_data(
    td_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("intent_management.delete")),
):
    await intent_service.delete_training_data(db, td_id)
