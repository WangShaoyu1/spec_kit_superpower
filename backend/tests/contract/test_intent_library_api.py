import time

from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_library(client: TestClient, token: str, library_key: str = "zh_core_v1") -> dict:
    response = client.post(
        "/api/v1/intent-libraries",
        headers=auth_headers(token),
        json={
            "library_key": library_key,
            "name": "中文指令库",
            "language": "zh",
            "description": "正式指令库",
            "default_thresholds": {
                "command_intent_accuracy_min": 0.95,
                "slot_f1_min": 0.9,
                "response_p95_ms": 2000,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["library"]


def test_create_library_returns_directory_and_rejects_duplicate_key(client: TestClient, admin_token: str):
    library = create_library(client, admin_token)

    assert library["library_key"] == "zh_core_v1"
    assert library["model_count"] == 0
    assert library["default_thresholds"]["command_intent_accuracy_min"] == 0.95

    list_response = client.get(
        "/api/v1/intent-libraries",
        headers=auth_headers(admin_token),
    )
    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert any(item["library_key"] == "zh_core_v1" for item in payload["items"])

    duplicate_response = client.post(
        "/api/v1/intent-libraries",
        headers=auth_headers(admin_token),
        json={
            "library_key": "zh_core_v1",
            "name": "重复指令库",
            "language": "zh",
            "description": "dup",
            "default_thresholds": {
                "command_intent_accuracy_min": 0.95,
                "slot_f1_min": 0.9,
                "response_p95_ms": 2000,
            },
        },
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["code"] == "LIB-409-KEY"


def test_library_detail_train_evaluate_publish_and_download_flow(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_train_v1")

    detail_response = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    training_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "training")
    evaluation_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "evaluation")
    assert training_dataset["sample_count"] == 39
    assert evaluation_dataset["sample_count"] == 39

    train_response = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={
            "training_dataset_id": training_dataset["id"],
            "version_name": "v1.0.0",
        },
    )
    assert train_response.status_code == 200
    model = train_response.json()["data"]["model"]
    assert model["status"] == "training"

    time.sleep(0.1)
    trained_detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    trained_model = next(item for item in trained_detail["models"] if item["id"] == model["id"])
    assert trained_model["status"] == "trained"

    evaluate_response = client.post(
        f"/api/v1/models/{model['id']}/evaluate",
        headers=auth_headers(admin_token),
        json={
            "evaluation_dataset_id": evaluation_dataset["id"],
            "threshold_override": {"slot_f1_min": 0.91},
        },
    )
    assert evaluate_response.status_code == 200
    run = evaluate_response.json()["data"]["evaluation_run"]
    assert run["status"] == "running"
    assert run["threshold_snapshot"]["slot_f1_min"] == 0.91

    time.sleep(0.1)
    evaluated_detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    evaluated_model = next(item for item in evaluated_detail["models"] if item["id"] == model["id"])
    assert evaluated_model["status"] == "testable"
    assert evaluated_model["is_testable"] is True
    assert evaluated_detail["evaluation_runs"][0]["analysis"]["summary"]

    publish_response = client.post(
        f"/api/v1/models/{model['id']}/publish",
        headers=auth_headers(admin_token),
        json={"note": "ready"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["model"]["is_published"] is True

    download_response = client.get(
        f"/api/v1/models/{model['id']}/download",
        headers=auth_headers(admin_token),
    )
    assert download_response.status_code == 200
    download_payload = download_response.json()["data"]
    assert download_payload["artifact_format"] == "zip"
    assert download_payload["artifact_uri"].endswith(".zip")


def test_single_test_returns_intent_slots_and_latency(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_test_v1")
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    training_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "training")

    model = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={"training_dataset_id": training_dataset["id"], "version_name": "v1.0.1"},
    ).json()["data"]["model"]

    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))

    response = client.post(
        f"/api/v1/models/{model['id']}/single-test",
        headers=auth_headers(admin_token),
        json={"utterance": "帮我打开烤箱，预热200度"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["intent"] == "device.on"
    assert payload["confidence"] >= 0.9
    assert payload["slots"]["device"] == "烤箱"
    assert payload["latency_ms"] > 0
    assert payload["model_id"] == model["id"]
    assert payload["model_version"] == "v1.0.1"
    assert payload["model_status"] in {"trained", "testable", "published"}


def test_dataset_detail_returns_samples_for_dataset_management_page(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_dataset_v1")
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "training")

    response = client.get(
        f"/api/v1/intent-libraries/{library['id']}/datasets/{dataset['id']}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["dataset"]["id"] == dataset["id"]
    assert payload["dataset"]["sample_count"] == dataset["sample_count"]
    assert len(payload["samples"]) == dataset["sample_count"]
    assert payload["samples"][0]["intent_key"]
    assert "display_name" in payload["samples"][0]


def test_library_can_be_deleted_from_directory(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_delete_v1")

    delete_response = client.delete(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    )
    assert delete_response.status_code == 200

    list_response = client.get(
        "/api/v1/intent-libraries",
        headers=auth_headers(admin_token),
    )
    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert all(item["id"] != library["id"] for item in payload["items"])


def test_published_library_cannot_be_deleted(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_published_v1")
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    training_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "training")
    evaluation_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "evaluation")

    model = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={"training_dataset_id": training_dataset["id"], "version_name": "v1.0.0"},
    ).json()["data"]["model"]
    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))
    client.post(
        f"/api/v1/models/{model['id']}/evaluate",
        headers=auth_headers(admin_token),
        json={"evaluation_dataset_id": evaluation_dataset["id"], "threshold_override": {"slot_f1_min": 0.91}},
    )
    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))
    client.post(
        f"/api/v1/models/{model['id']}/publish",
        headers=auth_headers(admin_token),
        json={"note": "ready"},
    )

    delete_response = client.delete(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    )
    assert delete_response.status_code == 409
    assert delete_response.json()["code"] == "LIB-409-PUBLISHED"


def test_dataset_catalog_and_dataset_detail_support_create_and_save(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_dataset_ops_v1")

    create_dataset_response = client.post(
        f"/api/v1/intent-libraries/{library['id']}/datasets",
        headers=auth_headers(admin_token),
        json={
            "name": "LLM扩充训练集",
            "dataset_type": "training",
            "source": "llm",
            "sample_count": 12,
        },
    )
    assert create_dataset_response.status_code == 200
    dataset = create_dataset_response.json()["data"]["dataset"]
    assert dataset["name"] == "LLM扩充训练集"
    assert dataset["source"] == "llm"
    assert dataset["sample_count"] == 12

    initial_detail_response = client.get(
        f"/api/v1/intent-libraries/{library['id']}/datasets/{dataset['id']}",
        headers=auth_headers(admin_token),
    )
    assert initial_detail_response.status_code == 200
    initial_detail_payload = initial_detail_response.json()["data"]
    assert len(initial_detail_payload["samples"]) == 12

    save_response = client.put(
        f"/api/v1/intent-libraries/{library['id']}/datasets/{dataset['id']}",
        headers=auth_headers(admin_token),
        json={
            "samples": [
                {
                    "intent_key": "device.on",
                    "display_name": "打开设备",
                    "required_slots": [{"name": "device"}],
                    "prompt_samples": ["打开烤箱"],
                    "negative_samples": ["不要打开烤箱"],
                    "entities": [{"entity_name": "device", "values": ["烤箱", "蒸箱"]}],
                }
            ]
        },
    )
    assert save_response.status_code == 200
    saved_payload = save_response.json()["data"]
    assert saved_payload["dataset"]["sample_count"] == 1
    assert saved_payload["samples"][0]["display_name"] == "打开设备"
    assert saved_payload["samples"][0]["entities"][0]["values"] == ["烤箱", "蒸箱"]

    detail_response = client.get(
        f"/api/v1/intent-libraries/{library['id']}/datasets/{dataset['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]
    assert detail_payload["samples"][0]["negative_samples"] == ["不要打开烤箱"]


def test_import_dataset_materializes_entries_in_detail(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_import_v1")

    create_response = client.post(
        f"/api/v1/intent-libraries/{library['id']}/datasets",
        headers=auth_headers(admin_token),
        json={
            "name": "导入训练集",
            "dataset_type": "training",
            "source": "import",
            "entries": ["打开烤箱", "关闭烤箱"],
        },
    )
    assert create_response.status_code == 200
    dataset = create_response.json()["data"]["dataset"]
    assert dataset["sample_count"] == 2

    detail_response = client.get(
        f"/api/v1/intent-libraries/{library['id']}/datasets/{dataset['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail_response.status_code == 200
    payload = detail_response.json()["data"]
    assert [item["display_name"] for item in payload["samples"]] == ["打开烤箱", "关闭烤箱"]


def test_train_model_rejects_empty_manual_dataset(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_empty_manual_v1")

    create_response = client.post(
        f"/api/v1/intent-libraries/{library['id']}/datasets",
        headers=auth_headers(admin_token),
        json={
            "name": "手工空训练集",
            "dataset_type": "training",
            "source": "manual",
        },
    )
    assert create_response.status_code == 200
    dataset = create_response.json()["data"]["dataset"]
    assert dataset["sample_count"] == 0

    response = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={"training_dataset_id": dataset["id"], "version_name": "v1.0.0"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "DATASET-422-EMPTY"


def test_save_dataset_detail_rejects_duplicate_intent_keys(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_duplicate_intent_v1")
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "training")

    response = client.put(
        f"/api/v1/intent-libraries/{library['id']}/datasets/{dataset['id']}",
        headers=auth_headers(admin_token),
        json={
            "samples": [
                {"intent_key": "device.on", "display_name": "打开设备"},
                {"intent_key": "device.on", "display_name": "重复意图"},
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "DATASET-422-INTENT-KEY"


def test_evaluate_model_rejects_invalid_threshold_override(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "zh_bad_threshold_v1")
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    training_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "training")
    evaluation_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "evaluation")

    model = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={"training_dataset_id": training_dataset["id"], "version_name": "v1.0.0"},
    ).json()["data"]["model"]
    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))

    response = client.post(
        f"/api/v1/models/{model['id']}/evaluate",
        headers=auth_headers(admin_token),
        json={
            "evaluation_dataset_id": evaluation_dataset["id"],
            "threshold_override": {"slot_f1_min": "bad-value"},
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "EVAL-422-THRESHOLD"
