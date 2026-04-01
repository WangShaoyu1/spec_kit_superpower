import time

from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_category(client: TestClient, token: str, name: str) -> dict:
    response = client.post(
        "/api/v1/knowledge-bases/categories",
        headers=auth_headers(token),
        json={"name": name, "icon": "🍳", "description": name},
    )
    assert response.status_code == 200
    return response.json()["data"]["category"]


def test_category_status_tracks_document_lifecycle(client: TestClient, admin_token: str):
    category = create_category(client, admin_token, "菜谱文档")

    upload = client.post(
        f"/api/v1/knowledge-bases/{category['id']}/documents/upload",
        headers=auth_headers(admin_token),
        json={
            "name": "红烧肉.json",
            "format": "json",
            "content": '{"recipe_name":"红烧肉","ingredients":["五花肉"],"steps":["切块","炖煮"]}',
        },
    )
    assert upload.status_code == 200
    assert upload.json()["data"]["document"]["status"] == "uploading"

    interim = client.get(
        f"/api/v1/knowledge-bases?category_id={category['id']}",
        headers=auth_headers(admin_token),
    )
    assert interim.status_code == 200
    assert interim.json()["data"]["categories"][0]["status"] in {"indexing", "ready"}

    time.sleep(0.1)
    final_state = client.get(
        f"/api/v1/knowledge-bases?category_id={category['id']}",
        headers=auth_headers(admin_token),
    )
    assert final_state.status_code == 200
    category_payload = final_state.json()["data"]["categories"][0]
    assert category_payload["status"] == "ready"
    assert category_payload["document_count"] == 1
    assert category_payload["ready_document_count"] == 1
