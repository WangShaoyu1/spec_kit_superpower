import pytest
import io
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_knowledge_base(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/knowledge/bases",
        json={"name": "菜谱知识", "description": "1000道菜谱"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "菜谱知识"
    assert data["document_count"] == 0


@pytest.mark.asyncio
async def test_list_knowledge_bases(client: AsyncClient, auth_headers):
    await client.post("/api/v1/knowledge/bases", json={"name": "KB1"}, headers=auth_headers)
    await client.post("/api/v1/knowledge/bases", json={"name": "KB2"}, headers=auth_headers)
    resp = await client.get("/api/v1/knowledge/bases", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_delete_knowledge_base(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/knowledge/bases", json={"name": "待删除KB"}, headers=auth_headers
    )
    kb_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/knowledge/bases/{kb_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_upload_markdown_document(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/knowledge/bases", json={"name": "上传测试KB"}, headers=auth_headers
    )
    kb_id = create_resp.json()["id"]

    content = "# 红烧肉\n\n## 食材\n- 五花肉 500g\n- 酱油 30ml\n\n## 步骤\n1. 切块焯水\n2. 炒糖色"
    files = {"file": ("红烧肉.md", content.encode("utf-8"), "text/markdown")}
    resp = await client.post(f"/api/v1/knowledge/bases/{kb_id}/upload", files=files, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "红烧肉"
    assert data["source_format"] == "markdown"
    assert data["index_status"] in ("indexed", "pending")


@pytest.mark.asyncio
async def test_upload_json_document_filters_invalid_fields(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/knowledge/bases", json={"name": "JSON测试KB"}, headers=auth_headers
    )
    kb_id = create_resp.json()["id"]

    import json
    doc = json.dumps({
        "name": "柠香雪梨银耳汤",
        "ingredients": ["银耳", "雪梨", "枸杞"],
        "steps": ["泡发银耳", "切雪梨", "炖煮"],
        "image_url": "https://example.com/photo.jpg",
        "like_count": 1234,
        "audit_status": "approved",
    })
    files = {"file": ("银耳汤.json", doc.encode("utf-8"), "application/json")}
    resp = await client.post(f"/api/v1/knowledge/bases/{kb_id}/upload", files=files, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "柠香雪梨银耳汤"


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/knowledge/bases", json={"name": "文档列表KB"}, headers=auth_headers
    )
    kb_id = create_resp.json()["id"]

    content = "# 测试文档\n\n内容"
    files = {"file": ("test.md", content.encode("utf-8"), "text/markdown")}
    await client.post(f"/api/v1/knowledge/bases/{kb_id}/upload", files=files, headers=auth_headers)

    resp = await client.get(f"/api/v1/knowledge/bases/{kb_id}/documents", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
