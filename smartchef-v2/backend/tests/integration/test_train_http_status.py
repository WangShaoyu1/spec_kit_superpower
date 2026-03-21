"""HTTP 训练：提交后 DB 已提交为 training，单行 GET 可见；后台任务 mock 避免真跑 torch。"""

import uuid
from unittest.mock import patch

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
async def test_post_train_get_model_shows_training_before_background_runs(client):
    """POST /train 之后立即 GET 必须为 training（与 BackgroundTasks 竞态修复：路由内 commit）。"""
    headers = await _auth(client)
    key = f"tr_{_uid()}"

    lib_resp = await client.post(
        PREFIX,
        json={"library_key": key, "name": "Train Status", "language": "en"},
        headers=headers,
    )
    assert lib_resp.status_code == 201
    lib_id = lib_resp.json()["data"]["id"]

    ds_resp = await client.post(
        f"{PREFIX}/{lib_id}/datasets",
        json={"name": "Train DS", "source_type": "manual"},
        headers=headers,
    )
    assert ds_resp.status_code == 201
    ds_id = ds_resp.json()["data"]["id"]

    intent_resp = await client.post(
        f"/api/v1/datasets/{ds_id}/intents",
        json={"intent_key": "greet", "name_zh": "问候", "slot_keys": []},
        headers=headers,
    )
    assert intent_resp.status_code == 201
    intent_id = intent_resp.json()["data"]["id"]

    for i in range(12):
        sq = await client.post(
            f"/api/v1/intents/{intent_id}/similar-questions",
            json={"text": f"hello test message number {i} for training min samples"},
            headers=headers,
        )
        assert sq.status_code == 201

    mv_resp = await client.post(
        f"{PREFIX}/{lib_id}/models",
        json={
            "version_name": f"v-{_uid()}",
            "train_dataset_id": ds_id,
            "train_config": {"base_model": "prajjwal1/bert-tiny", "max_epochs": 1, "epochs": 1},
        },
        headers=headers,
    )
    assert mv_resp.status_code == 201
    model_id = mv_resp.json()["data"]["id"]

    async def noop_bg(_mid, _url):
        return

    with patch("app.api.v1.model_versions._run_training_background", noop_bg):
        train_resp = await client.post(
            f"{MODEL_PREFIX}/{model_id}/train",
            json={"base_model": "prajjwal1/bert-tiny", "epochs": 1},
            headers=headers,
        )
        assert train_resp.status_code == 200, train_resp.text
        assert train_resp.json()["data"]["status"] == "training"

        get_resp = await client.get(f"{MODEL_PREFIX}/{model_id}", headers=headers)
        assert get_resp.status_code == 200
        body = get_resp.json()["data"]
        assert body["status"] == "training", (
            f"expected training in DB after route commit; got {body['status']} notes={body.get('notes')}"
        )
