"""Knowledge document CRUD, file upload, and status transitions."""

import os
import uuid as uuid_mod
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.core.config import get_settings
from app.models.knowledge import DocumentChunk, KnowledgeCategory, KnowledgeDocument

ALLOWED_FILE_TYPES = {"pdf", "txt", "docx", "xlsx", "json"}
UPLOAD_DIR = Path("uploads/knowledge")


async def list_documents(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    category_id: UUID | None = None,
    search: str | None = None,
    status: str | None = None,
) -> tuple[list[dict], int]:
    query = select(KnowledgeDocument)
    count_query = select(func.count()).select_from(KnowledgeDocument)

    if category_id:
        query = query.where(KnowledgeDocument.category_id == category_id)
        count_query = count_query.where(KnowledgeDocument.category_id == category_id)

    if search:
        pattern = f"%{search}%"
        query = query.where(KnowledgeDocument.title.ilike(pattern))
        count_query = count_query.where(KnowledgeDocument.title.ilike(pattern))

    if status:
        query = query.where(KnowledgeDocument.status == status)
        count_query = count_query.where(KnowledgeDocument.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(KnowledgeDocument.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    cat_ids = {r.category_id for r in rows if r.category_id}
    cat_names: dict[UUID, str] = {}
    if cat_ids:
        cats = (
            await db.execute(
                select(KnowledgeCategory.id, KnowledgeCategory.name)
                .where(KnowledgeCategory.id.in_(cat_ids))
            )
        ).all()
        cat_names = {c.id: c.name for c in cats}

    items = [_to_dict(doc, category_name=cat_names.get(doc.category_id)) for doc in rows]
    return items, total


async def upload_document(
    db: AsyncSession,
    *,
    title: str,
    category_id: UUID | None,
    file_content: bytes,
    filename: str,
    user_id: str,
) -> dict:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_FILE_TYPES:
        raise BusinessException("E60202", f"不支持的文件类型: {ext}，仅支持 {', '.join(sorted(ALLOWED_FILE_TYPES))}")

    if category_id:
        cat = await db.get(KnowledgeCategory, category_id)
        if not cat:
            raise BusinessException("E60101", "分类不存在")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid_mod.uuid4().hex}.{ext}"
    file_path = UPLOAD_DIR / stored_name

    file_path.write_bytes(file_content)

    doc = KnowledgeDocument(
        title=title,
        category_id=category_id,
        file_path=str(file_path),
        file_type=ext,
        file_size=len(file_content),
        status="uploading",
        created_by=user_id,
    )
    db.add(doc)
    await db.flush()

    doc.status = "parsing"
    await db.flush()

    try:
        chunks = _parse_document(file_content, ext)
        for idx, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                token_count=len(chunk_text.split()),
            )
            db.add(chunk)

        doc.chunk_count = len(chunks)
        doc.status = "ready"
    except Exception as exc:
        doc.status = "error"
        doc.error_message = str(exc)[:2000]

    await db.flush()
    return _to_dict(doc)


async def get_document(db: AsyncSession, document_id: UUID) -> dict:
    doc = await db.get(
        KnowledgeDocument,
        document_id,
        options=[selectinload(KnowledgeDocument.chunks)],
    )
    if not doc:
        raise BusinessException("E60201", "文档不存在")

    cat_name = None
    if doc.category_id:
        cat = await db.get(KnowledgeCategory, doc.category_id)
        cat_name = cat.name if cat else None

    result = _to_dict(doc, category_name=cat_name)
    result["chunks"] = [
        {
            "id": str(c.id),
            "document_id": str(c.document_id),
            "chunk_index": c.chunk_index,
            "content": c.content,
            "token_count": c.token_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in doc.chunks
    ]
    return result


async def update_document(
    db: AsyncSession, document_id: UUID, title: str | None, category_id: UUID | None,
) -> dict:
    doc = await db.get(KnowledgeDocument, document_id)
    if not doc:
        raise BusinessException("E60201", "文档不存在")

    if title is not None:
        doc.title = title
    if category_id is not None:
        cat = await db.get(KnowledgeCategory, category_id)
        if not cat:
            raise BusinessException("E60101", "分类不存在")
        doc.category_id = category_id

    await db.flush()
    return _to_dict(doc)


async def delete_document(db: AsyncSession, document_id: UUID) -> None:
    doc = await db.get(KnowledgeDocument, document_id)
    if not doc:
        raise BusinessException("E60201", "文档不存在")

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink(missing_ok=True)

    await db.delete(doc)
    await db.flush()


async def reindex_document(db: AsyncSession, document_id: UUID) -> dict:
    doc = await db.get(
        KnowledgeDocument,
        document_id,
        options=[selectinload(KnowledgeDocument.chunks)],
    )
    if not doc:
        raise BusinessException("E60201", "文档不存在")

    for chunk in list(doc.chunks):
        await db.delete(chunk)
    await db.flush()

    doc.status = "parsing"
    doc.error_message = None
    await db.flush()

    try:
        file_path = Path(doc.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件 {doc.file_path} 不存在")

        file_content = file_path.read_bytes()
        chunks = _parse_document(file_content, doc.file_type)

        for idx, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                token_count=len(chunk_text.split()),
            )
            db.add(chunk)

        doc.chunk_count = len(chunks)
        doc.status = "ready"
    except Exception as exc:
        doc.status = "error"
        doc.error_message = str(exc)[:2000]

    await db.flush()
    return _to_dict(doc)


def _parse_document(content: bytes, file_type: str) -> list[str]:
    """Simple text-based chunking. For txt files, split by double newline.
    For other types, treat the raw bytes as text (placeholder for real parsers)."""
    if file_type == "txt":
        text = content.decode("utf-8", errors="replace")
    else:
        text = content.decode("utf-8", errors="replace")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else ["(empty document)"]

    chunks = []
    current = ""
    max_chunk_chars = 1000
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chunk_chars and current:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)

    return chunks


def _to_dict(doc: KnowledgeDocument, *, category_name: str | None = None) -> dict:
    return {
        "id": str(doc.id),
        "title": doc.title,
        "category_id": str(doc.category_id) if doc.category_id else None,
        "category_name": category_name,
        "file_path": doc.file_path,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
        "created_by": str(doc.created_by) if doc.created_by else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }
