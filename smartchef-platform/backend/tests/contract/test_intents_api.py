import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_intent(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/intents",
        json={
            "intent_key": "voice_cmd_start_cooking",
            "display_name": "启动烹饪",
            "category": "烹饪控制",
            "description": "启动微波炉开始烹饪",
            "slots": [
                {
                    "slot_key": "duration",
                    "display_name": "时长",
                    "entity_type": "time",
                    "is_required": True,
                    "prompt_text": "请问您要加热多长时间？",
                }
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["intent_key"] == "voice_cmd_start_cooking"
    assert data["display_name"] == "启动烹饪"
    assert len(data["slots"]) == 1
    assert data["slots"][0]["slot_key"] == "duration"
    assert data["slots"][0]["is_required"] is True


@pytest.mark.asyncio
async def test_list_intents(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/intents",
        json={"intent_key": "test_intent_1", "display_name": "测试1", "category": "测试"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/intents",
        json={"intent_key": "test_intent_2", "display_name": "测试2", "category": "测试"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/intents", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_list_intents_filter_by_category(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/intents",
        json={"intent_key": "cat_a_1", "display_name": "A1", "category": "烹饪控制"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/intents",
        json={"intent_key": "cat_b_1", "display_name": "B1", "category": "菜谱操作"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/intents?category=烹饪控制", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["category"] == "烹饪控制"


@pytest.mark.asyncio
async def test_get_intent_detail(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/intents",
        json={"intent_key": "detail_test", "display_name": "详情测试", "category": "测试"},
        headers=auth_headers,
    )
    intent_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/intents/{intent_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["intent_key"] == "detail_test"


@pytest.mark.asyncio
async def test_update_intent(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/intents",
        json={"intent_key": "update_test", "display_name": "更新前", "category": "测试"},
        headers=auth_headers,
    )
    intent_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/api/v1/intents/{intent_id}",
        json={"display_name": "更新后", "category": "烹饪控制"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "更新后"
    assert resp.json()["category"] == "烹饪控制"


@pytest.mark.asyncio
async def test_delete_intent(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/intents",
        json={"intent_key": "delete_test", "display_name": "删除测试", "category": "测试"},
        headers=auth_headers,
    )
    intent_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/intents/{intent_id}", headers=auth_headers)
    assert resp.status_code == 204
    resp2 = await client.get(f"/api/v1/intents/{intent_id}", headers=auth_headers)
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_intent_key_rejected(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/intents",
        json={"intent_key": "dup_key", "display_name": "第一个", "category": "测试"},
        headers=auth_headers,
    )
    resp = await client.post(
        "/api/v1/intents",
        json={"intent_key": "dup_key", "display_name": "第二个", "category": "测试"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.get("/api/v1/intents")
    assert resp.status_code == 403
