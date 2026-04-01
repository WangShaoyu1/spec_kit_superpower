import time

from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_library(client: TestClient, token: str, library_key: str, name: str) -> dict:
    response = client.post(
        "/api/v1/intent-libraries",
        headers=auth_headers(token),
        json={
            "library_key": library_key,
            "name": name,
            "language": "zh",
            "description": f"{name}描述",
            "default_thresholds": {
                "command_intent_accuracy_min": 0.95,
                "slot_f1_min": 0.9,
                "response_p95_ms": 2000,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["library"]


def create_published_library(client: TestClient, token: str, library_key: str, name: str) -> dict:
    library = create_library(client, token, library_key, name)
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(token),
    )
    assert detail.status_code == 200
    training_dataset = next(
        item for item in detail.json()["data"]["datasets"] if item["dataset_type"] == "training"
    )
    train = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(token),
        json={"training_dataset_id": training_dataset["id"], "version_name": "v1.0.0"},
    )
    assert train.status_code == 200
    model = train.json()["data"]["model"]

    time.sleep(0.1)
    refreshed = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(token),
    )
    assert refreshed.status_code == 200
    evaluation_dataset = next(
        item for item in refreshed.json()["data"]["datasets"] if item["dataset_type"] == "evaluation"
    )
    evaluate = client.post(
        f"/api/v1/models/{model['id']}/evaluate",
        headers=auth_headers(token),
        json={"evaluation_dataset_id": evaluation_dataset["id"], "threshold_override": {}},
    )
    assert evaluate.status_code == 200

    time.sleep(0.1)
    evaluated = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(token),
    )
    assert evaluated.status_code == 200
    publish = client.post(
        f"/api/v1/models/{model['id']}/publish",
        headers=auth_headers(token),
        json={"note": "batch flow ready"},
    )
    assert publish.status_code == 200
    return library


def create_profile(client: TestClient, token: str, name: str, library_ids: list[str]) -> dict:
    response = client.post(
        "/api/v1/dialog-profiles",
        headers=auth_headers(token),
        json={
            "name": name,
            "llm_model": "gpt-4o-mini",
            "routing_strategy": "intent_first",
            "persona_name": "厨房助手",
            "persona_prompt": "活泼友好的厨房助手",
            "intent_threshold": 0.66,
            "session_timeout_minutes": 15,
            "knowledge_base_id": None,
            "library_ids": library_ids,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["profile"]


def create_batch(client: TestClient, token: str, profile_id: str, name: str) -> dict:
    response = client.post(
        "/api/v1/batch-tests",
        headers=auth_headers(token),
        json={
            "name": name,
            "profile_id": profile_id,
            "baseline_thresholds": {
                "accuracy_min": 0.95,
                "response_p95_ms": 2000,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["batch"]


def test_batch_run_status_tracks_case_generation_and_execution(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "batch_flow_a", "流程批测库A")
    profile = create_profile(client, admin_token, "流程批测方案A", [library["id"]])
    batch = create_batch(client, admin_token, profile["id"], "流程批次A")

    initial = client.get(
        f"/api/v1/batch-tests/{batch['id']}",
        headers=auth_headers(admin_token),
    )
    assert initial.status_code == 200
    assert initial.json()["data"]["batch"]["status"] == "draft"

    generate = client.post(
        f"/api/v1/batch-tests/{batch['id']}/generate-cases",
        headers=auth_headers(admin_token),
        json={"mode": "auto"},
    )
    assert generate.status_code == 200
    assert generate.json()["data"]["batch"]["status"] == "ready"

    execute = client.post(
        f"/api/v1/batch-tests/{batch['id']}/execute",
        headers=auth_headers(admin_token),
        json={},
    )
    assert execute.status_code == 200
    assert execute.json()["data"]["batch"]["status"] == "running"

    time.sleep(0.1)
    final_state = client.get(
        f"/api/v1/batch-tests/{batch['id']}",
        headers=auth_headers(admin_token),
    )
    assert final_state.status_code == 200
    final_payload = final_state.json()["data"]["batch"]
    assert final_payload["status"] == "completed"
    assert final_payload["executed_count"] == final_payload["case_count"]


def test_batch_metrics_and_analysis_consistency(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "batch_flow_b", "流程批测库B")
    profile = create_profile(client, admin_token, "流程批测方案B", [library["id"]])
    batch = create_batch(client, admin_token, profile["id"], "流程批次B")

    generate = client.post(
        f"/api/v1/batch-tests/{batch['id']}/generate-cases",
        headers=auth_headers(admin_token),
        json={"mode": "auto"},
    )
    assert generate.status_code == 200

    execute = client.post(
        f"/api/v1/batch-tests/{batch['id']}/execute",
        headers=auth_headers(admin_token),
        json={},
    )
    assert execute.status_code == 200

    time.sleep(0.1)
    detail = client.get(
        f"/api/v1/batch-tests/{batch['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 200
    payload = detail.json()["data"]
    batch_payload = payload["batch"]
    assert batch_payload["case_count"] == len(payload["cases"])
    assert batch_payload["executed_count"] == len(payload["results"])
    assert batch_payload["pass_count"] <= batch_payload["case_count"]
    assert payload["metrics"]["accuracy"] == batch_payload["accuracy"]
    assert payload["metrics"]["response_p95_ms"] == batch_payload["response_p95_ms"]
    assert payload["analysis"]["summary"]["total_cases"] == batch_payload["case_count"]
