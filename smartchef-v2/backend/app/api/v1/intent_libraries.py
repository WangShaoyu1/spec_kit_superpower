"""IntentLibrary CRUD routes (dd-intent-library.md §6.1)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import paginated_response, success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.schemas.intent_library import CreateLibraryRequest, UpdateLibraryRequest
from app.services import intent_library_service

router = APIRouter(prefix="/intent-libraries", tags=["intent-libraries"])


@router.get("")
async def list_libraries(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    items, total, total_zh, total_en = await intent_library_service.list_libraries(
        db, page=page, page_size=page_size, search=search, language=language,
    )
    return paginated_response(
        items, total=total, page=page, page_size=page_size,
        total_zh=total_zh, total_en=total_en,
    )


@router.post("")
@require_capability("intent_library_write")
async def create_library(
    request: Request,
    body: CreateLibraryRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await intent_library_service.create_library(db, body, user.user_id)
    return success_response(data, status_code=201)


@router.get("/{library_id}")
async def get_library(
    request: Request,
    library_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await intent_library_service.get_library(db, library_id)
    return success_response(data)


@router.put("/{library_id}")
@require_capability("intent_library_write")
async def update_library(
    request: Request,
    library_id: UUID,
    body: UpdateLibraryRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await intent_library_service.update_library(db, library_id, body)
    return success_response(data)


@router.delete("/{library_id}")
@require_capability("intent_library_delete")
async def delete_library(
    request: Request,
    library_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await intent_library_service.delete_library(db, library_id)
    return success_response(None, msg="删除成功")
