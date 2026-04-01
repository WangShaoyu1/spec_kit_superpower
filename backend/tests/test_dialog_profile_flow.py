import time

from fastapi.testclient import TestClient


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


def test_sessions_are_isolated_and_message_counts_track_history(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "dialog_flow_a", "流程库A")
    profile = create_profile(client, admin_token, "流程方案A", [library["id"]])

    session_a = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/test-sessions",
        headers=auth_headers(admin_token),
        json={"name": "会话A", "device_context": {"device_id": "device_a"}},
    )
    assert session_a.status_code == 200
    session_a_id = session_a.json()["data"]["session"]["id"]

    session_b = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/test-sessions",
        headers=auth_headers(admin_token),
        json={"name": "会话B", "device_context": {"device_id": "device_b"}},
    )
    assert session_b.status_code == 200
    session_b_id = session_b.json()["data"]["session"]["id"]

    send_a = client.post(
        f"/api/v1/test-sessions/{session_a_id}/messages",
        headers=auth_headers(admin_token),
        json={"text": "搜索红烧肉", "device_context": {"device_id": "device_a", "page": "recipe"}},
    )
    assert send_a.status_code == 200

    send_b = client.post(
        f"/api/v1/test-sessions/{session_b_id}/messages",
        headers=auth_headers(admin_token),
        json={"text": "开始烹饪", "device_context": {"device_id": "device_b", "page": "cook"}},
    )
    assert send_b.status_code == 200

    detail_a = client.get(f"/api/v1/test-sessions/{session_a_id}", headers=auth_headers(admin_token))
    detail_b = client.get(f"/api/v1/test-sessions/{session_b_id}", headers=auth_headers(admin_token))
    assert detail_a.status_code == 200
    assert detail_b.status_code == 200

    payload_a = detail_a.json()["data"]
    payload_b = detail_b.json()["data"]
    assert payload_a["session"]["message_count"] == 2
    assert payload_b["session"]["message_count"] == 2
    assert "红烧肉" in payload_a["messages"][0]["text"]
    assert "开始烹饪" in payload_b["messages"][0]["text"]
    assert all("红烧肉" not in item["text"] for item in payload_b["messages"])


def test_manual_test_trace_returns_route_intent_slots_model_and_device_context(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "dialog_flow_b", "流程库B")
    profile = create_profile(client, admin_token, "流程方案B", [library["id"]])

    session_response = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/test-sessions",
        headers=auth_headers(admin_token),
        json={
            "name": "上下文会话",
            "device_context": {"device_id": "device_ctx", "temperature": 200, "cooking": True},
        },
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["session"]["id"]

    send = client.post(
        f"/api/v1/test-sessions/{session_id}/messages",
        headers=auth_headers(admin_token),
        json={
            "text": "还有多久",
            "device_context": {"device_id": "device_ctx", "temperature": 200, "cooking": True},
        },
    )
    assert send.status_code == 200
    payload = send.json()["data"]
    trace = payload["debug_trace"]
    assert trace["route"]["type"] in {"knowledge", "fallback"}
    assert trace["route"]["confidence"] >= 0
    assert trace["intent"]["name"]
    assert trace["intent"]["confidence"] >= 0
    assert trace["model"] == "gpt-4o-mini"
    assert trace["response_text"] == payload["assistant_message"]["text"]
    assert trace["device_context_snapshot"]["temperature"] == 200
    assert payload["assistant_message"]["response_time_ms"] >= 0


def test_runtime_device_sessions_are_scoped_by_device_and_reuse_same_session(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "dialog_runtime_flow", "运行流程库")
    profile = create_profile(client, admin_token, "运行流程方案", [library["id"]])

    publish_profile = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_profile.status_code == 200

    first = client.post(
        "/api/v1/runtime/devices/device_flow_a/messages",
        headers=auth_headers(admin_token),
        json={"text": "开始烹饪", "device_context": {"page": "cook", "cooking": True}},
    )
    assert first.status_code == 200
    first_payload = first.json()["data"]

    second = client.post(
        "/api/v1/runtime/devices/device_flow_a/messages",
        headers=auth_headers(admin_token),
        json={"text": "还有多久", "device_context": {"page": "cook", "cooking": True}},
    )
    assert second.status_code == 200
    second_payload = second.json()["data"]

    other_device = client.post(
        "/api/v1/runtime/devices/device_flow_b/messages",
        headers=auth_headers(admin_token),
        json={"text": "开始烹饪", "device_context": {"page": "cook"}},
    )
    assert other_device.status_code == 200
    other_payload = other_device.json()["data"]

    assert first_payload["session_id"] == second_payload["session_id"]
    assert first_payload["session_id"] != other_payload["session_id"]


def test_runtime_english_input_without_english_library_does_not_fallback_to_chinese_intent(
    client: TestClient,
    admin_token: str,
):
    zh_library = create_published_library(client, admin_token, "dialog_lang_zh_only", "中文库", "zh")
    profile = create_profile(client, admin_token, "中文方案", [zh_library["id"]])

    publish_profile = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_profile.status_code == 200

    runtime = client.post(
        "/api/v1/runtime/devices/device_lang_a/messages",
        headers=auth_headers(admin_token),
        json={"text": "Start cooking", "device_context": {"page": "cook"}},
    )
    assert runtime.status_code == 200
    payload = runtime.json()["data"]
    assert payload["domain_type"] != "intent"
    assert "current" in payload["reply_text"].lower() or "kitchen assistant" in payload["reply_text"].lower()


def test_manual_mixed_language_input_prefers_chinese_routing(client: TestClient, admin_token: str):
    zh_library = create_published_library(client, admin_token, "dialog_lang_mixed_zh", "中文库M", "zh")
    en_library = create_published_library(client, admin_token, "dialog_lang_mixed_en", "English Lib M", "en")
    profile = create_profile(client, admin_token, "混合语言方案", [zh_library["id"], en_library["id"]])

    session_response = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/test-sessions",
        headers=auth_headers(admin_token),
        json={"name": "混合会话", "device_context": {"device_id": "device_mix"}},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["session"]["id"]

    send = client.post(
        f"/api/v1/test-sessions/{session_id}/messages",
        headers=auth_headers(admin_token),
        json={"text": "帮我 start cooking", "device_context": {"device_id": "device_mix"}},
    )
    assert send.status_code == 200
    payload = send.json()["data"]
    assert payload["debug_trace"]["route"]["type"] == "intent"
    assert "已收到" in payload["assistant_message"]["text"] or "指令已记录" in payload["assistant_message"]["text"]
