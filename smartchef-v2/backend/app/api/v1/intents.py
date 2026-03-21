"""Intent / Slot / Entity / SimilarQuestion / NegativeExample CRUD routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.schemas.intent_library import (
    CreateIntentRequest,
    CreateNegativeExampleRequest,
    CreateSimilarQuestionRequest,
    CreateSlotEntityRequest,
    CreateSlotRequest,
    UpdateIntentRequest,
    UpdateSimilarQuestionRequest,
    UpdateSlotEntityRequest,
    UpdateSlotRequest,
)
from app.services import intent_data_service

router = APIRouter(tags=["intents"])


# ---------------------------------------------------------------------------
# Intents
# ---------------------------------------------------------------------------

@router.get("/datasets/{dataset_id}/intents")
async def list_intents(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.list_intents(db, dataset_id)
    return success_response(data)


@router.post("/datasets/{dataset_id}/intents")
@require_capability("intent_library_write")
async def create_intent(
    request: Request,
    dataset_id: UUID,
    body: CreateIntentRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.create_intent(db, dataset_id, body)
    return success_response(data, status_code=201)


@router.get("/intents/{intent_id}")
async def get_intent(
    request: Request,
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.get_intent(db, intent_id)
    return success_response(data)


@router.put("/intents/{intent_id}")
@require_capability("intent_library_write")
async def update_intent(
    request: Request,
    intent_id: UUID,
    body: UpdateIntentRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.update_intent(db, intent_id, body)
    return success_response(data)


@router.delete("/intents/{intent_id}")
@require_capability("intent_library_delete")
async def delete_intent(
    request: Request,
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await intent_data_service.delete_intent(db, intent_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------

@router.get("/datasets/{dataset_id}/slots")
async def list_slots(
    request: Request,
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.list_slots(db, dataset_id)
    return success_response(data)


@router.post("/datasets/{dataset_id}/slots")
@require_capability("intent_library_write")
async def create_slot(
    request: Request,
    dataset_id: UUID,
    body: CreateSlotRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.create_slot(db, dataset_id, body)
    return success_response(data, status_code=201)


@router.get("/slots/{slot_id}")
async def get_slot(
    request: Request,
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.get_slot(db, slot_id)
    return success_response(data)


@router.put("/slots/{slot_id}")
@require_capability("intent_library_write")
async def update_slot(
    request: Request,
    slot_id: UUID,
    body: UpdateSlotRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.update_slot(db, slot_id, body)
    return success_response(data)


@router.delete("/slots/{slot_id}")
@require_capability("intent_library_delete")
async def delete_slot(
    request: Request,
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await intent_data_service.delete_slot(db, slot_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Slot Entities
# ---------------------------------------------------------------------------

@router.get("/slots/{slot_id}/entities")
async def list_entities(
    request: Request,
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.list_entities(db, slot_id)
    return success_response(data)


@router.post("/slots/{slot_id}/entities")
@require_capability("intent_library_write")
async def create_entity(
    request: Request,
    slot_id: UUID,
    body: CreateSlotEntityRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.create_entity(db, slot_id, body)
    return success_response(data, status_code=201)


@router.put("/entities/{entity_id}")
@require_capability("intent_library_write")
async def update_entity(
    request: Request,
    entity_id: UUID,
    body: UpdateSlotEntityRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.update_entity(db, entity_id, body)
    return success_response(data)


@router.delete("/entities/{entity_id}")
@require_capability("intent_library_delete")
async def delete_entity(
    request: Request,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await intent_data_service.delete_entity(db, entity_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Similar Questions
# ---------------------------------------------------------------------------

@router.get("/intents/{intent_id}/similar-questions")
async def list_similar_questions(
    request: Request,
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.list_similar_questions(db, intent_id)
    return success_response(data)


@router.post("/intents/{intent_id}/similar-questions")
@require_capability("intent_library_write")
async def create_similar_question(
    request: Request,
    intent_id: UUID,
    body: CreateSimilarQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.create_similar_question(db, intent_id, body)
    return success_response(data, status_code=201)


@router.put("/similar-questions/{sq_id}")
@require_capability("intent_library_write")
async def update_similar_question(
    request: Request,
    sq_id: UUID,
    body: UpdateSimilarQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.update_similar_question(db, sq_id, body)
    return success_response(data)


@router.delete("/similar-questions/{sq_id}")
@require_capability("intent_library_delete")
async def delete_similar_question(
    request: Request,
    sq_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await intent_data_service.delete_similar_question(db, sq_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Negative Examples
# ---------------------------------------------------------------------------

@router.get("/intents/{intent_id}/negative-examples")
async def list_negative_examples(
    request: Request,
    intent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_data_service.list_negative_examples(db, intent_id)
    return success_response(data)


@router.post("/intents/{intent_id}/negative-examples")
@require_capability("intent_library_write")
async def create_negative_example(
    request: Request,
    intent_id: UUID,
    body: CreateNegativeExampleRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_data_service.create_negative_example(db, intent_id, body)
    return success_response(data, status_code=201)


@router.delete("/negative-examples/{ne_id}")
@require_capability("intent_library_delete")
async def delete_negative_example(
    request: Request,
    ne_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await intent_data_service.delete_negative_example(db, ne_id)
    return success_response(None, msg="删除成功")
