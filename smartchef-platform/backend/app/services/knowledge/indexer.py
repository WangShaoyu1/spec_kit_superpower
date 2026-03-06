"""Vector indexer: generate embeddings and write to pgvector."""
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.knowledge.parser import parse_document

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for a text chunk.
    Uses a simple hash-based placeholder; replace with actual model call in production.
    """
    import hashlib
    h = hashlib.sha256(text.encode()).hexdigest()
    vector = []
    for i in range(0, min(len(h), 768 * 2), 2):
        val = int(h[i:i+2], 16) / 255.0 - 0.5
        vector.append(val)
    while len(vector) < 768:
        vector.append(0.0)
    return vector[:768]


async def index_document(db: AsyncSession, document_id: UUID) -> None:
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        logger.error(f"Document {document_id} not found")
        return

    try:
        doc.index_status = "indexing"
        await db.flush()

        _, _, _, chunks = parse_document(doc.content, doc.source_format)

        existing = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        for chunk in existing.scalars().all():
            await db.delete(chunk)
        await db.flush()

        for idx, chunk_text in enumerate(chunks):
            embedding = await generate_embedding(chunk_text)
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_index=idx,
                embedding=embedding,
            )
            db.add(chunk)

        doc.index_status = "indexed"
        await db.flush()
        logger.info(f"Indexed document {document_id}: {len(chunks)} chunks")

    except Exception as e:
        doc.index_status = "failed"
        await db.flush()
        logger.error(f"Failed to index document {document_id}: {e}")
        raise
