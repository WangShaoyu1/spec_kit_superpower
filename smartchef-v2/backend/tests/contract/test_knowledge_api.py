"""Contract tests for Knowledge Base API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.api_response import BusinessException
from tests.contract.conftest import make_auth_header

_DOC_UUID = str(uuid.uuid4())
_CAT_UUID = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_list_categories_200(client):
    headers = make_auth_header()
    with patch("app.api.v1.knowledge.category_service") as mock_cat:
        mock_cat.list_categories_tree = AsyncMock(return_value=[
            {"id": _CAT_UUID, "name": "Cat1", "children": [], "document_count": 0}
        ])
        resp = await client.get("/api/v1/knowledge/categories", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_create_category_201(client):
    headers = make_auth_header(["knowledge_write"])
    with patch("app.api.v1.knowledge.category_service") as mock_cat:
        mock_cat.create_category = AsyncMock(return_value={
            "id": _CAT_UUID, "name": "NewCat",
        })
        resp = await client.post(
            "/api/v1/knowledge/categories",
            json={"name": "NewCat"},
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name"] == "NewCat"


@pytest.mark.asyncio
async def test_delete_category_has_children_400(client):
    headers = make_auth_header(["knowledge_write"])
    with patch("app.api.v1.knowledge.category_service") as mock_cat:
        mock_cat.delete_category = AsyncMock(
            side_effect=BusinessException("E60102", "分类下有子分类或文档", http_status=400),
        )
        resp = await client.delete(
            f"/api/v1/knowledge/categories/{uuid.uuid4()}",
            headers=headers,
        )
    assert resp.status_code == 400
    assert resp.json()["code"] == "E60102"


@pytest.mark.asyncio
async def test_list_documents_200(client):
    headers = make_auth_header()
    with patch("app.api.v1.knowledge.document_service") as mock_doc:
        mock_doc.list_documents = AsyncMock(return_value=(
            [{"id": _DOC_UUID, "title": "Doc1"}], 1,
        ))
        resp = await client.get("/api/v1/knowledge/documents", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert "items" in body["data"]
    assert "total" in body["data"]


@pytest.mark.asyncio
async def test_get_document_404(client):
    headers = make_auth_header()
    with patch("app.api.v1.knowledge.document_service") as mock_doc:
        mock_doc.get_document = AsyncMock(
            side_effect=BusinessException("E60201", "文档不存在", http_status=404),
        )
        resp = await client.get(
            f"/api/v1/knowledge/documents/{uuid.uuid4()}",
            headers=headers,
        )
    assert resp.status_code == 404
    assert resp.json()["code"] == "E60201"


@pytest.mark.asyncio
async def test_delete_document_200(client):
    headers = make_auth_header(["knowledge_write"])
    with patch("app.api.v1.knowledge.document_service") as mock_doc:
        mock_doc.delete_document = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/knowledge/documents/{uuid.uuid4()}",
            headers=headers,
        )
    assert resp.status_code == 200
    assert resp.json()["code"] == "000000"


@pytest.mark.asyncio
async def test_search_200(client):
    headers = make_auth_header(["knowledge_read"])
    with patch("app.api.v1.knowledge.search_knowledge", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            {"chunk_id": str(uuid.uuid4()), "content": "answer", "score": 0.95},
        ]
        resp = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "how to cook rice"},
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get("/api/v1/knowledge/categories")
    assert resp.status_code == 401
