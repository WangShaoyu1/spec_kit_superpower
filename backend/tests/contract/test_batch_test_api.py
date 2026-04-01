import json
import time
import uuid

from fastapi.testclient import TestClient

from app.models import BatchTestCase, BatchTestRun


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_library(client: TestClient, token: str, library_key: str, name: str, language: str = "zh") -> dict:
    response = client.post(
        "/api/v1/intent-libraries",
        headers=auth_headers(token),
        json={
            "library_key": library_key,
            "name": name,
            "language": language,
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


def create_published_library(
    client: TestClient,
    token: str,
    library_key: str,
    name: str,
    language: str = "zh",
) -> dict:
    library = create_library(client, token, library_key, name, language)
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
        json={"note": "batch test ready"},
    )
    assert publish.status_code == 200
    return library


def create_profile(client: TestClient, token: str, name: str = "批测方案A", library_ids: list[str] | None = None) -> dict:
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
            "library_ids": library_ids or [],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["profile"]


def create_batch(client: TestClient, token: str, profile_id: str, name: str = "方案A-回归批次") -> dict:
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


def test_batch_directory_create_and_duplicate_guard(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "batch_lib_a", "批测库A")
    profile = create_profile(client, admin_token, "批测方案A", [library["id"]])
    batch = create_batch(client, admin_token, profile["id"])
    assert batch["name"] == "方案A-回归批次"
    assert batch["status"] == "draft"

    directory = client.get("/api/v1/batch-tests", headers=auth_headers(admin_token))
    assert directory.status_code == 200
    payload = directory.json()["data"]
    assert payload["summary"]["draft_count"] == 1
    assert any(item["name"] == "方案A-回归批次" for item in payload["items"])

    duplicate = client.post(
        "/api/v1/batch-tests",
        headers=auth_headers(admin_token),
        json={
            "name": "方案A-回归批次",
            "profile_id": profile["id"],
            "baseline_thresholds": {
                "accuracy_min": 0.95,
                "response_p95_ms": 2000,
            },
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "BATCH-409-NAME"


def test_generate_cases_execute_batch_and_read_detail(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "batch_lib_b", "批测库B")
    profile = create_profile(client, admin_token, "批测方案B", [library["id"]])
    batch = create_batch(client, admin_token, profile["id"], "方案B-批次")

    generated = client.post(
        f"/api/v1/batch-tests/{batch['id']}/generate-cases",
        headers=auth_headers(admin_token),
        json={"mode": "auto"},
    )
    assert generated.status_code == 200
    generated_payload = generated.json()["data"]
    assert generated_payload["batch"]["status"] == "ready"
    assert generated_payload["summary"]["case_count"] >= 3

    detail = client.get(
        f"/api/v1/batch-tests/{batch['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 200
    detail_payload = detail.json()["data"]
    assert len(detail_payload["cases"]) == generated_payload["summary"]["case_count"]
    assert detail_payload["results"] == []

    execute = client.post(
        f"/api/v1/batch-tests/{batch['id']}/execute",
        headers=auth_headers(admin_token),
        json={},
    )
    assert execute.status_code == 200
    assert execute.json()["data"]["batch"]["status"] == "running"

    time.sleep(0.1)
    detail_after = client.get(
        f"/api/v1/batch-tests/{batch['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail_after.status_code == 200
    after_payload = detail_after.json()["data"]
    assert after_payload["batch"]["status"] == "completed"
    assert after_payload["batch"]["executed_count"] == after_payload["batch"]["case_count"]
    assert len(after_payload["results"]) == after_payload["batch"]["executed_count"]


def test_batch_detail_returns_metrics_and_analysis_feedback(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "batch_lib_c", "批测库C")
    profile = create_profile(client, admin_token, "批测方案C", [library["id"]])
    batch = create_batch(client, admin_token, profile["id"], "方案C-分析批次")

    generated = client.post(
        f"/api/v1/batch-tests/{batch['id']}/generate-cases",
        headers=auth_headers(admin_token),
        json={"mode": "auto"},
    )
    assert generated.status_code == 200

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
    assert payload["metrics"]["accuracy"] >= 0
    assert payload["metrics"]["response_p95_ms"] >= 0
    assert payload["analysis"]["recommendations"]
    assert payload["analysis"]["root_causes"]


def test_batch_execution_uses_shared_language_routing_rules(client: TestClient, admin_token: str, app):
    zh_library = create_published_library(client, admin_token, "batch_lang_zh", "批测中文库", "zh")
    en_library = create_published_library(client, admin_token, "batch_lang_en", "Batch English Lib", "en")
    profile = create_profile(client, admin_token, "批测语言方案", [zh_library["id"], en_library["id"]])
    response = client.post(
        "/api/v1/batch-tests",
        headers=auth_headers(admin_token),
        json={
            "name": "语言路由批次",
            "profile_id": profile["id"],
            "baseline_thresholds": {
                "accuracy_min": 0.95,
                "command_response_p95_ms": 2000,
                "knowledge_response_p95_ms": 2000,
            },
        },
    )
    assert response.status_code == 200
    batch = response.json()["data"]["batch"]

    with app.state.session_factory() as session:
        batch_row = session.get(BatchTestRun, batch["id"])
        session.add_all(
            [
                BatchTestCase(
                    id=uuid.uuid4().hex,
                    batch_id=batch["id"],
                    case_no="CASE-LANG-001",
                    utterance="Start cooking",
                    expected_route="intent",
                    expected_intent="device.control",
                    expected_slots_json=json.dumps({}, ensure_ascii=False),
                    source="manual",
                    tuned=True,
                ),
                BatchTestCase(
                    id=uuid.uuid4().hex,
                    batch_id=batch["id"],
                    case_no="CASE-LANG-002",
                    utterance="帮我 start cooking",
                    expected_route="intent",
                    expected_intent="device.control",
                    expected_slots_json=json.dumps({}, ensure_ascii=False),
                    source="manual",
                    tuned=True,
                ),
            ]
        )
        batch_row.status = "ready"
        batch_row.case_count = 2
        session.commit()

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
    assert payload["batch"]["status"] == "completed"
    result_by_case = {item["case_id"]: item for item in payload["results"]}
    case_by_id = {item["id"]: item for item in payload["cases"]}
    resolved = {case_by_id[result_id]["utterance"]: result for result_id, result in result_by_case.items()}
    assert resolved["Start cooking"]["passed"] is True
    assert resolved["帮我 start cooking"]["passed"] is True


def test_batch_detail_uses_named_thresholds_and_route_specific_latency_budget(client: TestClient, admin_token: str, app):
    library = create_published_library(client, admin_token, "batch_threshold_zh", "阈值中文库", "zh")
    profile = create_profile(client, admin_token, "阈值方案", [library["id"]])
    response = client.post(
        "/api/v1/batch-tests",
        headers=auth_headers(admin_token),
        json={
            "name": "阈值批次",
            "profile_id": profile["id"],
            "baseline_thresholds": {
                "accuracy_min": 0.95,
                "command_response_p95_ms": 200,
                "knowledge_response_p95_ms": 2000,
            },
        },
    )
    assert response.status_code == 200
    batch = response.json()["data"]["batch"]

    with app.state.session_factory() as session:
        batch_row = session.get(BatchTestRun, batch["id"])
        session.add_all(
            [
                BatchTestCase(
                    id=uuid.uuid4().hex,
                    batch_id=batch["id"],
                    case_no="CASE-THRESHOLD-001",
                    utterance="开始烹饪",
                    expected_route="intent",
                    expected_intent="device.control",
                    expected_slots_json=json.dumps({}, ensure_ascii=False),
                    source="manual",
                    tuned=True,
                ),
                BatchTestCase(
                    id=uuid.uuid4().hex,
                    batch_id=batch["id"],
                    case_no="CASE-THRESHOLD-002",
                    utterance="怎么做红烧肉",
                    expected_route="knowledge",
                    expected_intent="knowledge.query",
                    expected_slots_json=json.dumps({}, ensure_ascii=False),
                    source="manual",
                    tuned=True,
                ),
            ]
        )
        batch_row.status = "ready"
        batch_row.case_count = 2
        session.commit()

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
    assert payload["batch"]["threshold_snapshot"]["command_response_p95_ms"] == 200
    assert payload["batch"]["threshold_snapshot"]["knowledge_response_p95_ms"] == 2000
    result_by_case = {item["case_id"]: item for item in payload["results"]}
    case_by_id = {item["id"]: item for item in payload["cases"]}
    resolved = {case_by_id[result_id]["utterance"]: result for result_id, result in result_by_case.items()}
    assert resolved["开始烹饪"]["failure_reason"] == "latency_exceeded"
    assert resolved["怎么做红烧肉"]["passed"] is True
