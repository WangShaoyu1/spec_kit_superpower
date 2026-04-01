import time

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import RequestLog


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
        json={"note": "dialog profile ready"},
    )
    assert publish.status_code == 200
    return library


def create_profile(client: TestClient, token: str, name: str = "方案A", library_ids: list[str] | None = None) -> dict:
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


def test_profile_directory_create_update_and_duplicate_guard(client: TestClient, admin_token: str):
    library = create_library(client, admin_token, "dialog_zh_a", "中文对话库A")
    profile = create_profile(client, admin_token, library_ids=[library["id"]])
    assert profile["name"] == "方案A"
    assert profile["status"] == "draft"

    directory = client.get("/api/v1/dialog-profiles", headers=auth_headers(admin_token))
    assert directory.status_code == 200
    payload = directory.json()["data"]
    assert payload["summary"]["draft_count"] == 1
    assert any(item["name"] == "方案A" for item in payload["items"])

    detail = client.get(
        f"/api/v1/dialog-profiles/{profile['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["bindings"][0]["library_id"] == library["id"]

    update = client.patch(
        f"/api/v1/dialog-profiles/{profile['id']}",
        headers=auth_headers(admin_token),
        json={
            "name": "方案A-正式",
            "llm_model": "gpt-4o",
            "routing_strategy": "hybrid",
            "persona_name": "专业顾问",
            "persona_prompt": "专业冷静的厨电顾问",
            "intent_threshold": 0.7,
            "session_timeout_minutes": 20,
            "knowledge_base_id": None,
            "library_ids": [library["id"]],
        },
    )
    assert update.status_code == 200
    updated = update.json()["data"]["profile"]
    assert updated["name"] == "方案A-正式"
    assert updated["llm_model"] == "gpt-4o"

    duplicate = client.post(
        "/api/v1/dialog-profiles",
        headers=auth_headers(admin_token),
        json={
            "name": "方案A-正式",
            "llm_model": "gpt-4o-mini",
            "routing_strategy": "intent_first",
            "persona_name": "助手",
            "persona_prompt": "测试",
            "intent_threshold": 0.66,
            "session_timeout_minutes": 15,
            "knowledge_base_id": None,
            "library_ids": [],
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "PROFILE-409-NAME"

    invalid = client.post(
        "/api/v1/dialog-profiles",
        headers=auth_headers(admin_token),
        json={
            "name": "非法阈值方案",
            "llm_model": "gpt-4o-mini",
            "routing_strategy": "intent_first",
            "persona_name": "助手",
            "persona_prompt": "测试",
            "intent_threshold": 1.2,
            "session_timeout_minutes": 15,
            "knowledge_base_id": None,
            "library_ids": [],
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "PROFILE-422-THRESHOLD"


def test_profile_publish_guard_and_publish_success_archives_previous(client: TestClient, admin_token: str):
    unready_library = create_library(client, admin_token, "dialog_zh_b", "中文对话库B")
    blocked = create_profile(client, admin_token, "待发布方案", [unready_library["id"]])

    publish_blocked = client.post(
        f"/api/v1/dialog-profiles/{blocked['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_blocked.status_code == 409
    blocked_payload = publish_blocked.json()
    assert blocked_payload["code"] == "PROFILE-409-PUBLISH-GATE"
    assert blocked_payload["data"]["guard_items"]

    ready_library = create_published_library(client, admin_token, "dialog_zh_c", "中文对话库C")
    profile_a = create_profile(client, admin_token, "方案发布A", [ready_library["id"]])
    publish_a = client.post(
        f"/api/v1/dialog-profiles/{profile_a['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_a.status_code == 200
    publish_payload_a = publish_a.json()["data"]
    assert publish_payload_a["profile"]["status"] == "published"
    assert publish_payload_a["profile"]["publish_version"] == 1
    assert publish_payload_a["guard_items"] == []

    profile_b = create_profile(client, admin_token, "方案发布B", [ready_library["id"]])
    publish_b = client.post(
        f"/api/v1/dialog-profiles/{profile_b['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_b.status_code == 200
    publish_payload_b = publish_b.json()["data"]
    assert publish_payload_b["profile"]["status"] == "published"
    assert publish_payload_b["profile"]["publish_version"] == 1

    detail_a = client.get(
        f"/api/v1/dialog-profiles/{profile_a['id']}",
        headers=auth_headers(admin_token),
    )
    assert detail_a.status_code == 200
    assert detail_a.json()["data"]["profile"]["status"] == "archived"

    directory = client.get("/api/v1/dialog-profiles", headers=auth_headers(admin_token))
    assert directory.status_code == 200
    directory_payload = directory.json()["data"]
    assert directory_payload["current_published_profile"]["id"] == profile_b["id"]
    assert directory_payload["summary"]["published_count"] == 1


def test_create_session_send_message_and_read_trace(client: TestClient, admin_token: str):
    ready_library = create_published_library(client, admin_token, "dialog_zh_d", "中文对话库D")
    profile = create_profile(client, admin_token, "测试方案", [ready_library["id"]])

    create_session = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/test-sessions",
        headers=auth_headers(admin_token),
        json={
            "name": "设备A会话",
            "device_context": {"device_id": "device_a", "page": "recipe", "cooking": True},
        },
    )
    assert create_session.status_code == 200
    session_payload = create_session.json()["data"]["session"]
    assert session_payload["message_count"] == 0

    send_message = client.post(
        f"/api/v1/test-sessions/{session_payload['id']}/messages",
        headers=auth_headers(admin_token),
        json={
            "text": "请帮我设置温度180度",
            "device_context": {"device_id": "device_a", "page": "recipe", "cooking": True},
        },
    )
    assert send_message.status_code == 200
    payload = send_message.json()["data"]
    assert payload["assistant_message"]["text"]
    assert payload["assistant_message"]["response_time_ms"] >= 0
    assert payload["debug_trace"]["route"]["type"] in {"intent", "knowledge", "fallback"}
    assert payload["debug_trace"]["route"]["confidence"] >= 0
    assert payload["debug_trace"]["intent"]["confidence"] >= 0
    assert payload["debug_trace"]["response_text"] == payload["assistant_message"]["text"]
    assert payload["debug_trace"]["device_context_snapshot"]["device_id"] == "device_a"
    assert payload["debug_trace"]["model"] == "gpt-4o-mini"
    assert payload["debug_trace"]["bindings"][0]["library_name"] == "中文对话库D"

    session_detail = client.get(
        f"/api/v1/test-sessions/{session_payload['id']}",
        headers=auth_headers(admin_token),
    )
    assert session_detail.status_code == 200
    detail_payload = session_detail.json()["data"]
    assert detail_payload["session"]["message_count"] == 2
    assert len(detail_payload["messages"]) == 2


def test_runtime_device_message_returns_production_contract_and_writes_request_log(
    client: TestClient,
    admin_token: str,
    app,
):
    ready_library = create_published_library(client, admin_token, "dialog_zh_runtime", "中文运行库")
    profile = create_profile(client, admin_token, "运行时方案", [ready_library["id"]])

    publish_profile = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_profile.status_code == 200

    runtime_response = client.post(
        "/api/v1/runtime/devices/device_runtime_a/messages",
        headers=auth_headers(admin_token),
        json={
            "text": "请帮我设置温度180度",
            "device_context": {
                "cooking": True,
                "door_closed": True,
                "page": "recipe",
                "screen": "main",
            },
        },
    )
    assert runtime_response.status_code == 200
    payload = runtime_response.json()["data"]
    assert payload["domain_type"] == "intent"
    assert payload["intent"]["name"] == "device.control"
    assert payload["slots"]["temperature"] == 180
    assert payload["reply_text"]
    assert payload["confidence"] >= 0
    assert payload["session_id"]
    assert payload["need_clarification"] is False
    assert payload["latency_ms"] >= 0
    assert payload["profile_version"] == 1

    with app.state.session_factory() as session:
        request_logs = session.execute(
            select(RequestLog).where(RequestLog.device_id == "device_runtime_a").order_by(RequestLog.created_at.asc())
        ).scalars().all()
        assert len(request_logs) == 1
        log = request_logs[0]
        assert log.session_id == payload["session_id"]
        assert log.route_type == "intent"
        assert log.intent_name == "device.control"
