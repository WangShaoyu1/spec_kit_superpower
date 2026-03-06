"""Knowledge QA generator: retrieval + LLM generation."""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.knowledge.retriever import search_knowledge
from app.services.chitchat.llm_adapter import chat_completion
from app.services.chitchat.persona import build_system_prompt

logger = logging.getLogger(__name__)

KNOWLEDGE_QA_THRESHOLD = 0.3


async def generate_knowledge_answer(
    db: AsyncSession,
    query: str,
    knowledge_base_ids: list[UUID] | None,
    persona_data: dict | None,
    model: str = "gpt-4o-mini",
) -> tuple[str | None, list[dict]]:
    """Try to answer from knowledge base. Returns (answer, hits) or (None, []) if no hit."""
    hits = []
    for kb_id in (knowledge_base_ids or []):
        results = await search_knowledge(db, query, kb_id, top_k=3)
        hits.extend(results)

    if not hits:
        return None, []

    relevant_hits = [h for h in hits if h["score"] >= KNOWLEDGE_QA_THRESHOLD]
    if not relevant_hits:
        return None, hits

    context_parts = []
    for h in relevant_hits[:3]:
        context_parts.append(f"[{h['document_title']}]\n{h['chunk_text']}")
    context = "\n\n".join(context_parts)

    system_prompt = build_system_prompt(persona_data)
    messages = [
        {"role": "system", "content": system_prompt + "\n\n请根据以下知识库内容回答用户的问题。如果知识库中没有相关信息，请如实告知。"},
        {"role": "user", "content": f"知识库参考内容：\n{context}\n\n用户问题：{query}"},
    ]

    answer = await chat_completion(messages, model=model, temperature=0.3)
    logger.info(f"Knowledge QA: query='{query[:30]}...' hits={len(relevant_hits)}")
    return answer, relevant_hits
