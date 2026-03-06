import pytest
from httpx import AsyncClient


@pytest.fixture
async def sample_intent(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/intents",
        json={
            "intent_key": "td_test_intent",
            "display_name": "训练数据测试意图",
            "category": "测试",
        },
        headers=auth_headers,
    )
    return resp.json()


@pytest.mark.asyncio
async def test_add_training_data(client: AsyncClient, auth_headers, sample_intent):
    intent_id = sample_intent["id"]
    resp = await client.post(
        f"/api/v1/intents/{intent_id}/training-data",
        json={"text": "帮我设置温度到180度", "language": "zh", "slot_annotations": None},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["text"] == "帮我设置温度到180度"
    assert data["language"] == "zh"


@pytest.mark.asyncio
async def test_batch_add_training_data(client: AsyncClient, auth_headers, sample_intent):
    intent_id = sample_intent["id"]
    resp = await client.post(
        f"/api/v1/intents/{intent_id}/training-data/batch",
        json=[
            {"text": "开始烹饪", "language": "zh"},
            {"text": "启动微波炉", "language": "zh"},
            {"text": "Start cooking", "language": "en"},
        ],
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_training_data(client: AsyncClient, auth_headers, sample_intent):
    intent_id = sample_intent["id"]
    await client.post(
        f"/api/v1/intents/{intent_id}/training-data",
        json={"text": "列表测试数据"},
        headers=auth_headers,
    )
    resp = await client.get(f"/api/v1/intents/{intent_id}/training-data", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_delete_training_data(client: AsyncClient, auth_headers, sample_intent):
    intent_id = sample_intent["id"]
    create_resp = await client.post(
        f"/api/v1/intents/{intent_id}/training-data",
        json={"text": "待删除"},
        headers=auth_headers,
    )
    td_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/intents/training-data/{td_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_training_data_with_slot_annotations(client: AsyncClient, auth_headers, sample_intent):
    intent_id = sample_intent["id"]
    annotations = [{"slot": "number", "start": 8, "end": 11, "value": "180"}]
    resp = await client.post(
        f"/api/v1/intents/{intent_id}/training-data",
        json={"text": "帮我设置温度到180度", "slot_annotations": annotations},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["slot_annotations"] == annotations
