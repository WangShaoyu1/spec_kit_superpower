"""Knowledge retriever: vector similarity search + reranking."""
import logging
from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import DocumentChunk, KnowledgeDocument
from app.services.knowledge.indexer import generate_embedding

logger = logging.getLogger(__name__)


async def search_knowledge(
    db: AsyncSession,
    query: str,
    knowledge_base_id: UUID | None = None,
    top_k: int = 5,
) -> list[dict]:
    query_embedding = await generate_embedding(query)

    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    sql = """
        SELECT dc.id, dc.chunk_text, dc.document_id,
               kd.title as document_title,
               dc.embedding <=> :embedding::vector AS distance
        FROM document_chunks dc
        JOIN knowledge_documents kd ON kd.id = dc.document_id
    """
    params = {"embedding": embedding_str}

    if knowledge_base_id:
        sql += " WHERE kd.knowledge_base_id = :kb_id"
        params["kb_id"] = str(knowledge_base_id)

    sql += " ORDER BY distance ASC LIMIT :top_k"
    params["top_k"] = top_k

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    results = []
    for row in rows:
        score = 1.0 - float(row.distance) if row.distance else 0.0
        results.append({
            "document_id": str(row.document_id),
            "document_title": row.document_title,
            "chunk_text": row.chunk_text,
            "score": round(score, 4),
        })

    return results
