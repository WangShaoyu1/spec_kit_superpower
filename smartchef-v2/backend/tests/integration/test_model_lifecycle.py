"""Integration test: model lifecycle API contract validation.

Tests API endpoints for the intent library module: library CRUD, dataset CRUD,
intent/SQ CRUD, model version CRUD, eval dataset CRUD.

NOTE: Real training/evaluation pipeline is tested in test_training_pipeline.py
which bypasses HTTP to avoid httpx.ASGITransport + BackgroundTasks deadlocks.
"""

import uuid

import pytest

from tests.integration.conftest import login_as_admin

PREFIX = "/api/v1/intent-libraries"
MODEL_PREFIX = "/api/v1/models"


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _auth(client) -> dict[str, str]:
    data = await login_as_admin(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.mark.asyncio(loop_scope="session")
async def test_library_crud(client):
    """Create, read, update, list libraries."""
    headers = await _auth(client)
    key = f"lib_{_uid()}"

    # Create
    resp = await client.post(PREFIX, json={
        "library_key": key, "name": "Test Lib", "language": "en",
    }, headers=headers)
    assert resp.status_code == 201
    lib_id = resp.json()["data"]["id"]

    # Read
    resp = await client.get(f"{PREFIX}/{lib_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["library_key"] == key

    # List (paginated)
    resp = await client.get(PREFIX, headers=headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any(lib["id"] == lib_id for lib in items)


@pytest.mark.asyncio(loop_scope="session")
async def test_dataset_and_intent_crud(client):
    """Create dataset, intents, similar questions with slot annotations."""
    headers = await _auth(client)
    key = f"ds_{_uid()}"

    lib_resp = await client.post(PREFIX, json={
        "library_key": key, "name": "DS Test Lib", "language": "en",
    }, headers=headers)
    lib_id = lib_resp.json()["data"]["id"]

    # Create training dataset
    ds_resp = await client.post(f"{PREFIX}/{lib_id}/datasets", json={
        "name": "Train DS", "source_type": "manual",
    }, headers=headers)
    assert ds_resp.status_code == 201
    ds_id = ds_resp.json()["data"]["id"]

    # Create intent
    i_resp = await client.post(f"/api/v1/datasets/{ds_id}/intents", json={
        "intent_key": "greet", "name_zh": "问候", "slot_keys": [],
    }, headers=headers)
    assert i_resp.status_code == 201
    intent_id = i_resp.json()["data"]["id"]

    # Create SQ without annotations
    sq1 = await client.post(
        f"/api/v1/intents/{intent_id}/similar-questions",
        json={"text": "Hello there"},
        headers=headers,
    )
    assert sq1.status_code == 201

    # Create SQ with list-style slot annotations
    sq2 = await client.post(
        f"/api/v1/intents/{intent_id}/similar-questions",
        json={
            "text": "Set a timer for 5 minutes",
            "slot_annotations": [{"start": 20, "end": 29, "slot": "duration"}],
        },
        headers=headers,
    )
    assert sq2.status_code == 201

    # Create SQ with dict-style slot annotations
    sq3 = await client.post(
        f"/api/v1/intents/{intent_id}/similar-questions",
        json={
            "text": "Play some music",
            "slot_annotations": {"genre": "pop"},
        },
        headers=headers,
    )
    assert sq3.status_code == 201

    # List intents
    list_resp = await client.get(f"/api/v1/datasets/{ds_id}/intents", headers=headers)
    assert list_resp.status_code == 200
    intents = list_resp.json()["data"]
    assert len(intents) >= 1


@pytest.mark.asyncio(loop_scope="session")
async def test_model_version_crud(client):
    """Create and list model versions for a library."""
    headers = await _auth(client)
    key = f"mv_{_uid()}"

    lib_resp = await client.post(PREFIX, json={
        "library_key": key, "name": "MV Test", "language": "en",
    }, headers=headers)
    lib_id = lib_resp.json()["data"]["id"]

    ds_resp = await client.post(f"{PREFIX}/{lib_id}/datasets", json={
        "name": "DS", "source_type": "manual",
    }, headers=headers)
    ds_id = ds_resp.json()["data"]["id"]

    # Create model version
    mv_resp = await client.post(f"{PREFIX}/{lib_id}/models", json={
        "version_name": f"v-{_uid()}",
        "train_dataset_id": ds_id,
        "train_config": {"base_model": "bert-base-chinese", "max_seq_length": 64},
        "notes": "Test model version",
    }, headers=headers)
    assert mv_resp.status_code == 201
    model_id = mv_resp.json()["data"]["id"]
    assert mv_resp.json()["data"]["status"] == "draft"
    # D045: 列表/详情「训练集」列依赖 train_dataset_name / dataset_name
    assert mv_resp.json()["data"]["train_dataset_name"] == "DS"
    assert mv_resp.json()["data"]["dataset_name"] == "DS"

    # Read model
    get_resp = await client.get(f"{MODEL_PREFIX}/{model_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["status"] == "draft"
    assert get_resp.json()["data"]["train_config"]["base_model"] == "bert-base-chinese"
    assert get_resp.json()["data"]["train_dataset_name"] == "DS"

    # List models
    list_resp = await client.get(f"{PREFIX}/{lib_id}/models", headers=headers)
    assert list_resp.status_code == 200
    models = list_resp.json()["data"]
    row = next(m for m in models if m["id"] == model_id)
    assert row["train_dataset_name"] == "DS"
    assert row["dataset_name"] == "DS"


@pytest.mark.asyncio(loop_scope="session")
async def test_eval_dataset_crud(client):
    """Create and update evaluation dataset with samples."""
    headers = await _auth(client)
    key = f"ev_{_uid()}"

    lib_resp = await client.post(PREFIX, json={
        "library_key": key, "name": "Eval Test", "language": "en",
    }, headers=headers)
    lib_id = lib_resp.json()["data"]["id"]

    # Create eval dataset
    eval_resp = await client.post(f"{PREFIX}/{lib_id}/eval-datasets", json={
        "name": "Eval DS", "source_type": "manual",
    }, headers=headers)
    assert eval_resp.status_code == 201
    eval_ds_id = eval_resp.json()["data"]["id"]

    # Update with samples
    samples = [
        {"utterance": "Hello!", "expected_result": "greet"},
        {"utterance": "Timer 8 minutes", "expected_result": "set_timer"},
    ]
    update_resp = await client.put(
        f"/api/v1/eval-datasets/{eval_ds_id}",
        json={"samples": samples},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["sample_count"] == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_generate_evaluation_dataset_rejects_library_mismatch(client):
    """Wrong library id must not generate against another library's eval dataset."""
    headers = await _auth(client)

    lib_resp = await client.post(PREFIX, json={
        "library_key": f"evsrc_{_uid()}", "name": "Eval Src", "language": "en",
    }, headers=headers)
    src_lib_id = lib_resp.json()["data"]["id"]

    other_lib_resp = await client.post(PREFIX, json={
        "library_key": f"evother_{_uid()}", "name": "Eval Other", "language": "en",
    }, headers=headers)
    other_lib_id = other_lib_resp.json()["data"]["id"]

    eval_resp = await client.post(f"{PREFIX}/{src_lib_id}/eval-datasets", json={
        "name": "Eval DS", "source_type": "manual",
    }, headers=headers)
    assert eval_resp.status_code == 201
    eval_ds_id = eval_resp.json()["data"]["id"]

    resp = await client.post(
        f"{PREFIX}/{other_lib_id}/eval-datasets/{eval_ds_id}/generate",
        json={"model_name": "gpt-4o", "samples_per_intent": 20},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "E50502"
