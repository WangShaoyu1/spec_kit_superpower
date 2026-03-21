"""Contract tests for app.api.v1.intents — slots, entities, similar Q, negative examples."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.contract.conftest import make_auth_header

DS_ID = str(uuid.uuid4())
SLOT_ID = str(uuid.uuid4())
ENTITY_ID = str(uuid.uuid4())
INTENT_ID = str(uuid.uuid4())
SQ_ID = str(uuid.uuid4())
NE_ID = str(uuid.uuid4())
PATCH_SVC = "app.api.v1.intents.intent_data_service"


@pytest.mark.asyncio
async def test_list_slots_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_slots = AsyncMock(return_value=[
            {"id": SLOT_ID, "slot_key": "duration", "name_zh": "时长"},
        ])
        resp = await client.get(
            f"/api/v1/datasets/{DS_ID}/slots",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_create_slot_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {
        "slot_key": "duration",
        "name_zh": "时长",
        "slot_type": "text",
    }
    with patch(PATCH_SVC) as svc:
        svc.create_slot = AsyncMock(return_value={"id": SLOT_ID, **payload})
        resp = await client.post(
            f"/api/v1/datasets/{DS_ID}/slots",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == SLOT_ID


@pytest.mark.asyncio
async def test_get_slot_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.get_slot = AsyncMock(return_value={
            "id": SLOT_ID, "slot_key": "duration", "name_zh": "时长",
        })
        resp = await client.get(f"/api/v1/slots/{SLOT_ID}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == SLOT_ID


@pytest.mark.asyncio
async def test_update_slot_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"name_zh": "持续时间"}
    with patch(PATCH_SVC) as svc:
        svc.update_slot = AsyncMock(return_value={
            "id": SLOT_ID, "slot_key": "duration", **payload,
        })
        resp = await client.put(
            f"/api/v1/slots/{SLOT_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["name_zh"] == "持续时间"


@pytest.mark.asyncio
async def test_delete_slot_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_slot = AsyncMock(return_value=None)
        resp = await client.delete(f"/api/v1/slots/{SLOT_ID}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_list_entities_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_entities = AsyncMock(return_value=[
            {"id": ENTITY_ID, "value": "5分钟", "slot_id": SLOT_ID},
        ])
        resp = await client.get(
            f"/api/v1/slots/{SLOT_ID}/entities",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_create_entity_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"value": "5分钟", "synonyms": "five minutes"}
    with patch(PATCH_SVC) as svc:
        svc.create_entity = AsyncMock(return_value={
            "id": ENTITY_ID, "slot_id": SLOT_ID, "value": "5分钟",
        })
        resp = await client.post(
            f"/api/v1/slots/{SLOT_ID}/entities",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"
    assert body["data"]["id"] == ENTITY_ID


@pytest.mark.asyncio
async def test_update_entity_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"value": "十分钟"}
    with patch(PATCH_SVC) as svc:
        svc.update_entity = AsyncMock(return_value={
            "id": ENTITY_ID, "value": "十分钟", "slot_id": SLOT_ID,
        })
        resp = await client.put(
            f"/api/v1/entities/{ENTITY_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_delete_entity_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_entity = AsyncMock(return_value=None)
        resp = await client.delete(f"/api/v1/entities/{ENTITY_ID}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_list_similar_questions_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_similar_questions = AsyncMock(return_value=[
            {"id": SQ_ID, "text": "hello", "intent_id": INTENT_ID},
        ])
        resp = await client.get(
            f"/api/v1/intents/{INTENT_ID}/similar-questions",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_create_similar_question_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"text": "hello", "slot_annotations": {}}
    with patch(PATCH_SVC) as svc:
        svc.create_similar_question = AsyncMock(return_value={
            "id": SQ_ID, "intent_id": INTENT_ID, "text": "hello",
        })
        resp = await client.post(
            f"/api/v1/intents/{INTENT_ID}/similar-questions",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_update_similar_question_200(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"text": "hi there"}
    with patch(PATCH_SVC) as svc:
        svc.update_similar_question = AsyncMock(return_value={
            "id": SQ_ID, "text": "hi there", "intent_id": INTENT_ID,
        })
        resp = await client.put(
            f"/api/v1/similar-questions/{SQ_ID}",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_delete_similar_question_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_similar_question = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/similar-questions/{SQ_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_list_negative_examples_200(client):
    headers = make_auth_header()
    with patch(PATCH_SVC) as svc:
        svc.list_negative_examples = AsyncMock(return_value=[
            {"id": NE_ID, "text": "不是问候", "intent_id": INTENT_ID},
        ])
        resp = await client.get(
            f"/api/v1/intents/{INTENT_ID}/negative-examples",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_create_negative_example_201(client):
    headers = make_auth_header(["intent_library_write"])
    payload = {"text": "不是问候"}
    with patch(PATCH_SVC) as svc:
        svc.create_negative_example = AsyncMock(return_value={
            "id": NE_ID, "intent_id": INTENT_ID, "text": "不是问候",
        })
        resp = await client.post(
            f"/api/v1/intents/{INTENT_ID}/negative-examples",
            json=payload,
            headers=headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_delete_negative_example_200(client):
    headers = make_auth_header(["intent_library_delete"])
    with patch(PATCH_SVC) as svc:
        svc.delete_negative_example = AsyncMock(return_value=None)
        resp = await client.delete(
            f"/api/v1/negative-examples/{NE_ID}",
            headers=headers,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "000000"


@pytest.mark.asyncio
async def test_no_auth_401(client):
    resp = await client.get(f"/api/v1/datasets/{DS_ID}/slots")
    assert resp.status_code == 401
