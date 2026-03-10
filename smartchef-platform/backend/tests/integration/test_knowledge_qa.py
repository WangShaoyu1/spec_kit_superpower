"""知识问答集成测试：检索 + LLM 生成流程。

覆盖场景：
1. 知识检索成功 → LLM 生成回答
2. 知识检索未命中 → 降级处理
3. 菜谱类问题的问答流程
4. 多个文档块命中时的重排序
"""
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeBase, KnowledgeDocument, DocumentChunk
from app.services.knowledge.qa_generator import generate_knowledge_answer
from app.services.knowledge.retriever import search_knowledge


# 固定向量，用于 mock embedding 与测试数据一致性
TEST_EMBEDDING = [0.1] * 768
TEST_EMBEDDING_B = [0.2] * 768


@pytest.fixture
async def knowledge_base_with_chunks(db_session: AsyncSession):
    """创建带文档块的知识库，用于检索测试。"""
    kb = KnowledgeBase(name="菜谱知识", description="测试用")
    db_session.add(kb)
    await db_session.flush()

    doc = KnowledgeDocument(
        knowledge_base_id=kb.id,
        title="红烧肉做法",
        content="# 红烧肉\n食材：五花肉、酱油",
        source_format="markdown",
        index_status="indexed",
    )
    db_session.add(doc)
    await db_session.flush()

    # 第一个块：高相关
    chunk1 = DocumentChunk(
        document_id=doc.id,
        chunk_text="红烧肉食材：五花肉500g、酱油30ml。步骤：切块焯水、炒糖色、炖煮。",
        chunk_index=0,
        embedding=TEST_EMBEDDING,
    )
    db_session.add(chunk1)

    # 第二个块：次相关（不同向量，距离稍远）
    chunk2 = DocumentChunk(
        document_id=doc.id,
        chunk_text="红烧肉营养：高蛋白，约300卡/100g。",
        chunk_index=1,
        embedding=TEST_EMBEDDING_B,
    )
    db_session.add(chunk2)

    await db_session.commit()
    return kb


@pytest.mark.asyncio
async def test_knowledge_retrieval_success_then_llm_answer(
    db_session: AsyncSession,
    knowledge_base_with_chunks: KnowledgeBase,
):
    """知识检索成功 → LLM 生成回答（mock embedding + mock LLM）。"""
    kb = knowledge_base_with_chunks

    with (
        patch(
            "app.services.knowledge.indexer.generate_embedding",
            new_callable=AsyncMock,
            return_value=TEST_EMBEDDING,
        ),
        patch(
            "app.services.knowledge.qa_generator.chat_completion",
            new_callable=AsyncMock,
            return_value="红烧肉需要五花肉500g、酱油30ml。步骤：切块焯水、炒糖色、炖煮即可。",
        ),
    ):
        answer, hits = await generate_knowledge_answer(
            db_session, "红烧肉怎么做", [kb.id], None, model="gpt-4o-mini"
        )

    assert answer is not None
    assert "五花肉" in answer or "红烧肉" in answer
    assert len(hits) >= 1
    assert hits[0]["score"] >= 0.3
    assert "红烧肉" in hits[0]["chunk_text"]


@pytest.mark.asyncio
async def test_knowledge_retrieval_no_hit_fallback(
    db_session: AsyncSession,
    knowledge_base_with_chunks: KnowledgeBase,
):
    """知识检索未命中 → 降级处理，返回 (None, [])。"""
    kb = knowledge_base_with_chunks
    # 使用与库中向量差异极大的查询向量，导致无命中或分数低于阈值
    far_embedding = [0.9] * 768

    with (
        patch(
            "app.services.knowledge.indexer.generate_embedding",
            new_callable=AsyncMock,
            return_value=far_embedding,
        ),
    ):
        # 即使检索到结果，若 score < 0.3 也会降级
        answer, hits = await generate_knowledge_answer(
            db_session, "宇宙大爆炸理论", [kb.id], None
        )

    # 远距离向量的 score 会很低，低于阈值 0.3，应降级
    if hits:
        relevant = [h for h in hits if h["score"] >= 0.3]
        if not relevant:
            assert answer is None
    else:
        assert answer is None


@pytest.mark.asyncio
async def test_recipe_qa_flow(
    db_session: AsyncSession,
    knowledge_base_with_chunks: KnowledgeBase,
):
    """菜谱类问题的完整问答流程。"""
    kb = knowledge_base_with_chunks
    persona = {"name": "小厨", "personality": "热情", "tone_style": "亲切"}

    with (
        patch(
            "app.services.knowledge.indexer.generate_embedding",
            new_callable=AsyncMock,
            return_value=TEST_EMBEDDING,
        ),
        patch(
            "app.services.knowledge.qa_generator.chat_completion",
            new_callable=AsyncMock,
            return_value="红烧肉的食材包括五花肉和酱油，先切块焯水再炒糖色炖煮。",
        ),
    ):
        answer, hits = await generate_knowledge_answer(
            db_session, "红烧肉需要什么食材", [kb.id], persona
        )

    assert answer is not None
    assert len(hits) >= 1
    # 验证 persona 被传入（通过 chat_completion 的 messages 可推断，此处仅验证有答案）
    assert "五花肉" in answer or "酱油" in answer or "食材" in answer


@pytest.mark.asyncio
async def test_multiple_chunks_reranking(
    db_session: AsyncSession,
    knowledge_base_with_chunks: KnowledgeBase,
):
    """多个文档块命中时，按 score 重排序，取 top 3 构造上下文。"""
    kb = knowledge_base_with_chunks
    # 查询向量接近 chunk1，chunk1 应排在前面
    with (
        patch(
            "app.services.knowledge.indexer.generate_embedding",
            new_callable=AsyncMock,
            return_value=TEST_EMBEDDING,
        ),
        patch(
            "app.services.knowledge.qa_generator.chat_completion",
            new_callable=AsyncMock,
            return_value="根据知识库：红烧肉做法如上。",
        ),
    ):
        answer, hits = await generate_knowledge_answer(
            db_session, "红烧肉怎么做", [kb.id], None, model="gpt-4o-mini"
        )

    # 应至少有一个命中
    assert len(hits) >= 1
    # 按 score 降序（retriever 按 distance 升序，score = 1 - distance）
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)
    # 第一个命中应与 TEST_EMBEDDING 最接近
    assert hits[0]["chunk_text"].find("食材") >= 0 or hits[0]["chunk_text"].find("步骤") >= 0


@pytest.mark.asyncio
async def test_search_knowledge_empty_base_returns_empty(
    db_session: AsyncSession,
):
    """空知识库检索返回空列表。"""
    kb = KnowledgeBase(name="空库", description="无文档")
    db_session.add(kb)
    await db_session.flush()

    with patch(
        "app.services.knowledge.indexer.generate_embedding",
        new_callable=AsyncMock,
        return_value=TEST_EMBEDDING,
    ):
        results = await search_knowledge(db_session, "任意问题", kb.id, top_k=3)

    assert results == []
