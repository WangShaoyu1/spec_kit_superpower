"""Knowledge base management service: CRUD + document upload + async indexing."""
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.knowledge import KnowledgeBase, KnowledgeDocument, DocumentChunk
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.services.knowledge.parser import parse_document
from app.services.knowledge.indexer import index_document


async def list_knowledge_bases(db: AsyncSession) -> list[KnowledgeBase]:
    result = await db.execute(
        select(KnowledgeBase).options(selectinload(KnowledgeBase.documents)).order_by(KnowledgeBase.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def get_knowledge_base(db: AsyncSession, kb_id: UUID) -> KnowledgeBase:
    result = await db.execute(
        select(KnowledgeBase).options(selectinload(KnowledgeBase.documents)).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return kb


async def create_knowledge_base(db: AsyncSession, data: KnowledgeBaseCreate, user_id: UUID | None = None) -> KnowledgeBase:
    kb = KnowledgeBase(name=data.name, description=data.description, created_by=user_id)
    db.add(kb)
    await db.flush()
    await db.refresh(kb)
    return kb


async def update_knowledge_base(db: AsyncSession, kb_id: UUID, data: KnowledgeBaseUpdate) -> KnowledgeBase:
    kb = await get_knowledge_base(db, kb_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(kb, key, value)
    await db.flush()
    return kb


async def delete_knowledge_base(db: AsyncSession, kb_id: UUID) -> None:
    kb = await get_knowledge_base(db, kb_id)
    await db.delete(kb)
    await db.flush()


async def upload_document(
    db: AsyncSession,
    kb_id: UUID,
    filename: str,
    raw_content: str,
    source_format: str,
) -> KnowledgeDocument:
    await get_knowledge_base(db, kb_id)

    title, content, metadata, _ = parse_document(raw_content, source_format)

    doc = KnowledgeDocument(
        knowledge_base_id=kb_id,
        title=title,
        content=content,
        source_format=source_format,
        source_filename=filename,
        metadata_=metadata,
        index_status="pending",
    )
    db.add(doc)
    await db.flush()

    await index_document(db, doc.id)

    await db.refresh(doc)
    return doc


async def get_document(db: AsyncSession, doc_id: UUID) -> KnowledgeDocument:
    result = await db.execute(
        select(KnowledgeDocument)
        .options(selectinload(KnowledgeDocument.chunks))
        .where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return doc


async def delete_document(db: AsyncSession, doc_id: UUID) -> None:
    doc = await get_document(db, doc_id)
    await db.delete(doc)
    await db.flush()


async def list_documents(db: AsyncSession, kb_id: UUID) -> list[KnowledgeDocument]:
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.knowledge_base_id == kb_id)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return list(result.scalars().all())
