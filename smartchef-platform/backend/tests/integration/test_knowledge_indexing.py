"""文档解析与索引集成测试：parser、indexer、retriever 协作验证。"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.knowledge import KnowledgeBase, KnowledgeDocument, DocumentChunk
from app.services.knowledge.parser import (
    parse_markdown_document,
    chunk_text,
    parse_document,
    CHUNK_SIZE,
)
from app.services.knowledge.indexer import index_document
from app.services.knowledge.retriever import search_knowledge


# --- 1. JSON 文档解析 → 过滤无效字段 → 生成文本块 ---


def test_json_parse_filters_invalid_fields_and_generates_chunks():
    """JSON 解析应过滤无效字段（image_url、like_count 等），并生成有效文本块。"""
    raw = json.dumps({
        "name": "柠香雪梨银耳汤",
        "ingredients": ["银耳", "雪梨", "枸杞"],
        "steps": ["泡发银耳", "切雪梨", "炖煮"],
        "image_url": "https://example.com/photo.jpg",
        "like_count": 1234,
        "audit_status": "approved",
    })
    title, content, metadata, chunks = parse_document(raw, "json")

    assert title == "柠香雪梨银耳汤"
    assert "image_url" not in content and "like_count" not in content
    assert "audit_status" not in content
    assert "ingredients" in content and "steps" in content
    assert len(chunks) >= 1
    assert all(isinstance(c, str) and len(c) > 0 for c in chunks)


def test_json_parse_with_nested_invalid_fields():
    """嵌套对象中的无效字段应被递归过滤。"""
    raw = json.dumps({
        "name": "红烧肉",
        "detail": {
            "view_count": 999,
            "description": "经典家常菜",
        },
    })
    title, content, metadata, chunks = parse_document(raw, "json")

    assert "view_count" not in content
    assert "description" in content or "detail" in content


# --- 2. Markdown 文档解析 → 按标题分块 ---


def test_markdown_parse_extracts_title_and_chunks():
    """Markdown 解析应提取标题，并将全文分块。"""
    raw = """# 红烧肉

## 食材
- 五花肉 500g
- 酱油 30ml

## 步骤
1. 切块焯水
2. 炒糖色
"""
    title, content, metadata, chunks = parse_document(raw, "markdown")

    assert title == "红烧肉"
    assert "## 食材" in content and "## 步骤" in content
    assert len(chunks) >= 1


def test_markdown_parse_extracts_json_blocks_as_metadata():
    """Markdown 中的 ```json 代码块应被解析为 metadata。"""
    raw = """# 菜谱

正文内容

```json
{"source": "家常菜", "category": "川菜"}
```
"""
    title, content, metadata = parse_markdown_document(raw)

    assert "source" in metadata or "category" in metadata


# --- 3. 文本分块边界情况 ---


def test_chunk_text_empty_document():
    """空文档应返回空列表或单元素列表（空字符串被 strip 后可能为空）。"""
    # chunk_text 对空字符串：len("") <= 500，返回 [text] 即 [""]
    # 但 chunk 会 strip，空 chunk 不会被添加
    result = chunk_text("")
    assert result == [""]

    # 仅有空白
    result = chunk_text("   \n\t   ")
    assert len(result) >= 1


def test_chunk_text_short_document_returns_single_chunk():
    """短于 CHUNK_SIZE 的文档应返回单个块。"""
    short = "这是短文本"
    result = chunk_text(short)
    assert result == [short]


def test_chunk_text_long_document_splits_with_overlap():
    """超长文档应按 chunk_size 分块，含 overlap。"""
    long_text = "x" * (CHUNK_SIZE * 3)
    chunks = chunk_text(long_text)
    assert len(chunks) >= 2
    # 每块应非空
    assert all(len(c) > 0 for c in chunks)


# --- 4. 索引流程：文档上传 → 解析 → 生成 chunks ---


@pytest.fixture
async def knowledge_base(db_session):
    """创建测试用知识库。"""
    kb = KnowledgeBase(name="集成测试KB", description="用于索引测试")
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.mark.asyncio
async def test_index_flow_creates_chunks_in_db(db_session, knowledge_base):
    """索引流程：创建文档 → 解析 → 生成 chunks 并写入数据库。"""
    content = "# 测试菜谱\n\n食材：五花肉、酱油。步骤：切块、炒糖色。"
    doc = KnowledgeDocument(
        knowledge_base_id=knowledge_base.id,
        title="测试菜谱",
        content=content,
        source_format="markdown",
        source_filename="test.md",
        index_status="pending",
    )
    db_session.add(doc)
    await db_session.flush()

    await index_document(db_session, doc.id)
    await db_session.flush()

    result = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    assert len(chunks) >= 1
    assert doc.index_status == "indexed"
    for i, ch in enumerate(chunks):
        assert ch.chunk_index == i
        assert ch.chunk_text
        assert ch.embedding is not None
        assert len(ch.embedding) == 768


@pytest.mark.asyncio
async def test_index_flow_json_document(db_session, knowledge_base):
    """JSON 文档索引后应产生正确 chunks。"""
    raw = json.dumps({
        "name": "番茄炒蛋",
        "ingredients": ["番茄", "鸡蛋", "盐"],
        "steps": ["切番茄", "打蛋", "翻炒"],
    })
    title, content, metadata, _ = parse_document(raw, "json")
    doc = KnowledgeDocument(
        knowledge_base_id=knowledge_base.id,
        title=title,
        content=content,
        source_format="json",
        source_filename="番茄炒蛋.json",
        metadata_=metadata,
        index_status="pending",
    )
    db_session.add(doc)
    await db_session.flush()

    await index_document(db_session, doc.id)
    await db_session.flush()

    result = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunks = result.scalars().all()
    assert len(chunks) >= 1
    combined = " ".join(c.chunk_text for c in chunks)
    assert "番茄" in combined or "鸡蛋" in combined


@pytest.mark.asyncio
async def test_index_replaces_existing_chunks_on_reindex(db_session, knowledge_base):
    """重新索引时应删除旧 chunks 并写入新 ones。"""
    content = "# 初版\n内容A"
    doc = KnowledgeDocument(
        knowledge_base_id=knowledge_base.id,
        title="初版",
        content=content,
        source_format="markdown",
        index_status="pending",
    )
    db_session.add(doc)
    await db_session.flush()

    await index_document(db_session, doc.id)
    await db_session.flush()

    # 更新内容并重新索引
    doc.content = "# 修订版\n内容B，更长一些以便产生不同分块"
    await db_session.flush()
    await index_document(db_session, doc.id)
    await db_session.flush()

    result2 = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunks2 = result2.scalars().all()
    assert all("修订版" in c.chunk_text or "内容B" in c.chunk_text for c in chunks2)


# --- 5. 检索流程：验证返回格式 ---


@pytest.mark.asyncio
async def test_retrieval_return_format(db_session, knowledge_base):
    """检索应返回 list[dict]，含 document_id、document_title、chunk_text、score。"""
    content = "# 宫保鸡丁\n\n经典川菜，鸡肉丁配花生。"
    doc = KnowledgeDocument(
        knowledge_base_id=knowledge_base.id,
        title="宫保鸡丁",
        content=content,
        source_format="markdown",
        index_status="pending",
    )
    db_session.add(doc)
    await db_session.flush()
    await index_document(db_session, doc.id)
    await db_session.flush()

    results = await search_knowledge(
        db_session,
        query="宫保鸡丁怎么做",
        knowledge_base_id=knowledge_base.id,
        top_k=5,
    )

    assert isinstance(results, list)
    for r in results:
        assert "document_id" in r
        assert "document_title" in r
        assert "chunk_text" in r
        assert "score" in r
        assert isinstance(r["score"], (int, float))
        assert 0 <= r["score"] <= 1


@pytest.mark.asyncio
async def test_retrieval_with_mock_embedding(db_session, knowledge_base):
    """mock embedding 后检索仍返回正确格式。"""
    content = "# 鱼香肉丝\n食材：里脊、木耳。"
    doc = KnowledgeDocument(
        knowledge_base_id=knowledge_base.id,
        title="鱼香肉丝",
        content=content,
        source_format="markdown",
        index_status="pending",
    )
    db_session.add(doc)
    await db_session.flush()

    # mock embedding 为固定向量，避免外部 API 调用
    fake_vector = [0.1] * 768

    with patch(
        "app.services.knowledge.indexer.generate_embedding",
        new_callable=AsyncMock,
        return_value=fake_vector,
    ):
        await index_document(db_session, doc.id)

    with patch(
        "app.services.knowledge.retriever.generate_embedding",
        new_callable=AsyncMock,
        return_value=fake_vector,
    ):
        results = await search_knowledge(
            db_session,
            query="鱼香肉丝",
            knowledge_base_id=knowledge_base.id,
            top_k=3,
        )

    assert isinstance(results, list)
    for r in results:
        assert "document_id" in r and "document_title" in r
        assert "chunk_text" in r and "score" in r
