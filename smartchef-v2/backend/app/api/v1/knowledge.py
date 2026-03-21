"""Knowledge Base API routes — categories, documents, and search."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException, paginated_response, success_response
from app.core.database import get_db
from app.core.security import get_current_user_from_token, require_capability
from app.schemas.knowledge import (
    CreateCategoryRequest,
    SearchRequest,
    UpdateCategoryRequest,
    UpdateDocumentRequest,
)
from app.services.knowledge import category_service, document_service
from app.services.knowledge.retriever import search_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@router.get("/categories")
async def list_categories(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    tree = await category_service.list_categories_tree(db)
    return success_response(tree)


@router.post("/categories")
@require_capability("knowledge_write")
async def create_category(
    request: Request,
    body: CreateCategoryRequest,
    db: AsyncSession = Depends(get_db),
):
    user = request.state.current_user
    data = await category_service.create_category(db, body, user.user_id)
    return success_response(data, status_code=201)


@router.put("/categories/{category_id}")
@require_capability("knowledge_write")
async def update_category(
    request: Request,
    category_id: UUID,
    body: UpdateCategoryRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await category_service.update_category(db, category_id, body)
    return success_response(data)


@router.delete("/categories/{category_id}")
@require_capability("knowledge_write")
async def delete_category(
    request: Request,
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await category_service.delete_category(db, category_id)
    return success_response(None, msg="删除成功")


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@router.get("/documents")
async def list_documents(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: UUID | None = Query(None),
    search: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    items, total = await document_service.list_documents(
        db, page=page, page_size=page_size,
        category_id=category_id, search=search, status=status,
    )
    return paginated_response(items, total=total, page=page, page_size=page_size)


@router.post("/documents")
@require_capability("knowledge_write")
async def upload_document(
    request: Request,
    title: str = Form(...),
    category_id: UUID | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    MAX_FILE_SIZE = 10 * 1024 * 1024
    user = request.state.current_user
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise BusinessException("E60203", "文件大小超过限制(10MB)", http_status=413)
    data = await document_service.upload_document(
        db,
        title=title,
        category_id=category_id,
        file_content=content,
        filename=file.filename or "unknown",
        user_id=user.user_id,
    )
    return success_response(data, status_code=201)


@router.get("/documents/{document_id}")
async def get_document(
    request: Request,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_current_user_from_token(request)
    data = await document_service.get_document(db, document_id)
    return success_response(data)


@router.put("/documents/{document_id}")
@require_capability("knowledge_write")
async def update_document(
    request: Request,
    document_id: UUID,
    body: UpdateDocumentRequest,
    db: AsyncSession = Depends(get_db),
):
    data = await document_service.update_document(
        db, document_id, body.title, body.category_id,
    )
    return success_response(data)


@router.delete("/documents/{document_id}")
@require_capability("knowledge_write")
async def delete_document(
    request: Request,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await document_service.delete_document(db, document_id)
    return success_response(None, msg="删除成功")


@router.post("/documents/{document_id}/reindex")
@require_capability("knowledge_write")
async def reindex_document(
    request: Request,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await document_service.reindex_document(db, document_id)
    return success_response(data)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.post("/search")
@require_capability("knowledge_read")
async def search(
    request: Request,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    hits = await search_knowledge(
        db, query=body.query, category_id=body.category_id, top_k=body.top_k,
    )
    return success_response(hits)
