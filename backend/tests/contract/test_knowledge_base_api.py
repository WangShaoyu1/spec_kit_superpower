import time

from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_category(client: TestClient, token: str, name: str = "菜谱知识") -> dict:
    response = client.post(
        "/api/v1/knowledge-bases/categories",
        headers=auth_headers(token),
        json={"name": name, "icon": "🍳", "description": f"{name}描述"},
    )
    assert response.status_code == 200
    return response.json()["data"]["category"]


def upload_document(
    client: TestClient,
    token: str,
    category_id: str,
    *,
    name: str = "银耳汤.json",
    format: str = "json",
    content: str = '{"recipe_name":"柠香雪梨银耳汤","ingredients":["银耳","雪梨"],"steps":["泡发","炖煮"],"image_url":"https://img","like_count":2}',
) -> dict:
    response = client.post(
        f"/api/v1/knowledge-bases/{category_id}/documents/upload",
        headers=auth_headers(token),
        json={"name": name, "format": format, "content": content},
    )
    assert response.status_code == 200
    return response.json()["data"]["document"]


def test_category_directory_create_update_and_duplicate_guard(client: TestClient, admin_token: str):
    category = create_category(client, admin_token)
    assert category["name"] == "菜谱知识"
    assert category["status"] == "empty"

    directory = client.get("/api/v1/knowledge-bases", headers=auth_headers(admin_token))
    assert directory.status_code == 200
    payload = directory.json()["data"]
    assert any(item["name"] == "菜谱知识" for item in payload["categories"])
    assert payload["documents"] == []

    update_response = client.patch(
        f"/api/v1/knowledge-bases/categories/{category['id']}",
        headers=auth_headers(admin_token),
        json={"name": "菜谱知识库", "icon": "📚", "description": "更新后描述"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["category"]["name"] == "菜谱知识库"

    duplicate = client.post(
        "/api/v1/knowledge-bases/categories",
        headers=auth_headers(admin_token),
        json={"name": "菜谱知识库", "icon": "🍳", "description": "dup"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "KB-CAT-409-NAME"


def test_upload_detail_retrieve_and_delete_document_flow(client: TestClient, admin_token: str):
    category = create_category(client, admin_token, "公司信息")
    document = upload_document(
        client,
        admin_token,
        category["id"],
        name="公司简介.md",
        format="markdown",
        content="# 公司简介\nSmartChef 是智能厨房平台。\n## 联系方式\n客服电话 400-800-1234",
    )
    assert document["status"] == "uploading"

    time.sleep(0.1)
    directory = client.get(
        f"/api/v1/knowledge-bases?category_id={category['id']}",
        headers=auth_headers(admin_token),
    )
    assert directory.status_code == 200
    doc_item = directory.json()["data"]["documents"][0]
    assert doc_item["status"] == "ready"
    assert doc_item["index_version"] == 1

    detail = client.get(
        f"/api/v1/knowledge-documents/{doc_item['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 200
    detail_payload = detail.json()["data"]
    assert detail_payload["document"]["name"] == "公司简介.md"
    assert detail_payload["valid_content"]
    assert detail_payload["filtered_fields"] == []

    retrieve = client.post(
        f"/api/v1/knowledge-documents/{doc_item['id']}/retrieve-test",
        headers=auth_headers(admin_token),
        json={"query": "客服电话"},
    )
    assert retrieve.status_code == 200
    retrieve_payload = retrieve.json()["data"]
    assert retrieve_payload["hit"] is True
    assert retrieve_payload["score"] > 0
    assert "客服电话" in retrieve_payload["snippet"]

    delete_response = client.request(
        "DELETE",
        f"/api/v1/knowledge-documents/{doc_item['id']}",
        headers=auth_headers(admin_token),
    )
    assert delete_response.status_code == 200

    after_delete = client.get(
        f"/api/v1/knowledge-bases?category_id={category['id']}",
        headers=auth_headers(admin_token),
    )
    assert after_delete.status_code == 200
    assert after_delete.json()["data"]["documents"] == []


def test_json_filtering_and_reindex_version_increment(client: TestClient, admin_token: str):
    category = create_category(client, admin_token, "产品指南")
    document = upload_document(client, admin_token, category["id"])

    time.sleep(0.1)
    detail = client.get(
        f"/api/v1/knowledge-documents/{document['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 200
    detail_payload = detail.json()["data"]
    assert any(item["field"] == "image_url" for item in detail_payload["filtered_fields"])
    assert any(item["field"] == "recipe_name" for item in detail_payload["valid_content"])

    reindex = client.post(
        f"/api/v1/knowledge-documents/{document['id']}/reindex",
        headers=auth_headers(admin_token),
        json={"reason": "refresh"},
    )
    assert reindex.status_code == 200
    assert reindex.json()["data"]["document"]["status"] == "indexing"

    time.sleep(0.1)
    detail_after = client.get(
        f"/api/v1/knowledge-documents/{document['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail_after.status_code == 200
    assert detail_after.json()["data"]["document"]["index_version"] == 2
