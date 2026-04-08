import time

from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_evaluation_run_snapshots_thresholds_and_promotes_single_testable_model(client: TestClient, admin_token: str):
    create_response = client.post(
        "/api/v1/intent-libraries",
        headers=auth_headers(admin_token),
        json={
            "library_key": "flow_lib_v1",
            "name": "流转库",
            "language": "zh",
            "description": "flow",
            "default_thresholds": {
                "command_intent_accuracy_min": 0.95,
                "slot_f1_min": 0.9,
                "response_p95_ms": 2000,
            },
        },
    )
    library = create_response.json()["data"]["library"]
    detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    training_datasets = [item for item in detail["datasets"] if item["dataset_type"] == "training"]
    evaluation_dataset = next(item for item in detail["datasets"] if item["dataset_type"] == "evaluation")

    first_model = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={"training_dataset_id": training_datasets[0]["id"], "version_name": "v1.0.0"},
    ).json()["data"]["model"]
    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))
    client.post(
        f"/api/v1/models/{first_model['id']}/evaluate",
        headers=auth_headers(admin_token),
        json={"evaluation_dataset_id": evaluation_dataset["id"], "threshold_override": {"slot_f1_min": 0.92}},
    )
    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))

    second_model = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(admin_token),
        json={"training_dataset_id": training_datasets[1]["id"], "version_name": "v1.0.1"},
    ).json()["data"]["model"]
    time.sleep(0.1)
    client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(admin_token))
    client.post(
        f"/api/v1/models/{second_model['id']}/evaluate",
        headers=auth_headers(admin_token),
        json={"evaluation_dataset_id": evaluation_dataset["id"], "threshold_override": {"slot_f1_min": 0.91}},
    )
    time.sleep(0.1)

    final_detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    first_detail = next(item for item in final_detail["models"] if item["id"] == first_model["id"])
    second_detail = next(item for item in final_detail["models"] if item["id"] == second_model["id"])

    assert first_detail["is_testable"] is False
    assert second_detail["is_testable"] is True
    assert final_detail["evaluation_runs"][0]["threshold_snapshot"]["slot_f1_min"] in {0.91, 0.92}
    assert final_detail["evaluation_runs"][0]["metrics"]["command_intent_accuracy"] >= 0.95


def test_evaluation_falls_back_to_trained_when_thresholds_are_not_met(client: TestClient, admin_token: str):
    create_response = client.post(
        "/api/v1/intent-libraries",
        headers=auth_headers(admin_token),
        json={
            "library_key": "flow_lib_v2",
            "name": "高阈值流转库",
            "language": "zh",
            "description": "flow",
            "default_thresholds": {
                "command_intent_accuracy_min": 0.95,
                "slot_f1_min": 0.9,
                "response_p95_ms": 2000,
            },
        },
    )
    library = create_response.json()["data"]["library"]
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
        json={
            "evaluation_dataset_id": evaluation_dataset["id"],
            "threshold_override": {"slot_f1_min": 0.99},
        },
    )
    time.sleep(0.1)

    final_detail = client.get(
        f"/api/v1/intent-libraries/{library['id']}",
        headers=auth_headers(admin_token),
    ).json()["data"]
    model_detail = next(item for item in final_detail["models"] if item["id"] == model["id"])

    assert model_detail["status"] == "trained"
    assert model_detail["is_testable"] is False
