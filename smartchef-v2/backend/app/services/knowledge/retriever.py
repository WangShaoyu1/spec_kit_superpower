"""Placeholder semantic search service.

Uses simple text matching for now. Will be replaced with vector search
once pgvector / embedding pipeline is integrated.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import DocumentChunk, KnowledgeDocument


async def search_knowledge(
    db: AsyncSession,
    *,
    query: str,
    category_id: UUID | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Simple keyword-based search across document chunks."""
    pattern = f"%{query}%"

    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.content,
            KnowledgeDocument.title.label("document_title"),
        )
        .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeDocument.status == "ready")
        .where(DocumentChunk.content.ilike(pattern))
    )

    if category_id:
        stmt = stmt.where(KnowledgeDocument.category_id == category_id)

    stmt = stmt.limit(top_k)
    result = await db.execute(stmt)
    rows = result.all()

    hits = []
    for row in rows:
        content_lower = row.content.lower()
        query_lower = query.lower()
        occurrences = content_lower.count(query_lower)
        score = min(1.0, occurrences * 0.2)

        hits.append({
            "chunk_id": str(row.id),
            "document_id": str(row.document_id),
            "document_title": row.document_title,
            "chunk_index": row.chunk_index,
            "content": row.content,
            "score": round(score, 4),
        })

    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits
