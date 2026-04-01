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
