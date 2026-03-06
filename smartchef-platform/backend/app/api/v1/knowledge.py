from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseInfo, KnowledgeBaseUpdate,
    KnowledgeDocumentInfo, KnowledgeSearchRequest, KnowledgeSearchResult,
)
from app.services.knowledge import service as kb_service
from app.services.knowledge.retriever import search_knowledge

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


@router.get("/bases", response_model=list[KnowledgeBaseInfo])
async def list_bases(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.read")),
):
    bases = await kb_service.list_knowledge_bases(db)
    return [
        KnowledgeBaseInfo(
            id=kb.id, name=kb.name, description=kb.description,
            document_count=len(kb.documents),
            created_at=kb.created_at, updated_at=kb.updated_at,
        )
        for kb in bases
    ]


@router.post("/bases", response_model=KnowledgeBaseInfo, status_code=201)
async def create_base(
    body: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("knowledge_management.write")),
):
    kb = await kb_service.create_knowledge_base(db, body, current_user.id)
    return KnowledgeBaseInfo(
        id=kb.id, name=kb.name, description=kb.description,
        document_count=0, created_at=kb.created_at, updated_at=kb.updated_at,
    )


@router.patch("/bases/{kb_id}", response_model=KnowledgeBaseInfo)
async def update_base(
    kb_id: UUID, body: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.write")),
):
    kb = await kb_service.update_knowledge_base(db, kb_id, body)
    return KnowledgeBaseInfo(
        id=kb.id, name=kb.name, description=kb.description,
        document_count=len(kb.documents),
        created_at=kb.created_at, updated_at=kb.updated_at,
    )


@router.delete("/bases/{kb_id}", status_code=204)
async def delete_base(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.delete")),
):
    await kb_service.delete_knowledge_base(db, kb_id)


@router.get("/bases/{kb_id}/documents", response_model=list[KnowledgeDocumentInfo])
async def list_documents(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.read")),
):
    docs = await kb_service.list_documents(db, kb_id)
    return [
        KnowledgeDocumentInfo(
            id=d.id, title=d.title, content=d.content[:200] + "..." if len(d.content) > 200 else d.content,
            source_format=d.source_format, source_filename=d.source_filename,
            metadata_=d.metadata_, index_status=d.index_status,
            chunk_count=0, created_at=d.created_at,
        )
        for d in docs
    ]


@router.post("/bases/{kb_id}/upload", response_model=KnowledgeDocumentInfo, status_code=201)
async def upload_document(
    kb_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.write")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    raw = await file.read()
    content = raw.decode("utf-8")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "md"
    source_format = "json" if ext == "json" else "markdown"

    doc = await kb_service.upload_document(db, kb_id, file.filename, content, source_format)
    return KnowledgeDocumentInfo(
        id=doc.id, title=doc.title, content=doc.content[:200] + "...",
        source_format=doc.source_format, source_filename=doc.source_filename,
        metadata_=doc.metadata_, index_status=doc.index_status,
        chunk_count=len(doc.chunks) if doc.chunks else 0,
        created_at=doc.created_at,
    )


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.delete")),
):
    await kb_service.delete_document(db, doc_id)


@router.post("/search", response_model=list[KnowledgeSearchResult])
async def search(
    body: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("knowledge_management.read")),
):
    results = await search_knowledge(db, body.query, body.knowledge_base_id, body.top_k)
    return [KnowledgeSearchResult(**r) for r in results]
