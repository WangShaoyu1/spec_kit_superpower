import os
import time

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app import models


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Abc12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


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
    detail = client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(token))
    assert detail.status_code == 200
    training_dataset = next(item for item in detail.json()["data"]["datasets"] if item["dataset_type"] == "training")

    train = client.post(
        f"/api/v1/intent-libraries/{library['id']}/models/train",
        headers=auth_headers(token),
        json={"training_dataset_id": training_dataset["id"], "version_name": "v1.0.0"},
    )
    assert train.status_code == 200
    model = train.json()["data"]["model"]

    time.sleep(0.1)
    refreshed = client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(token))
    assert refreshed.status_code == 200
    evaluation_dataset = next(item for item in refreshed.json()["data"]["datasets"] if item["dataset_type"] == "evaluation")

    evaluate = client.post(
        f"/api/v1/models/{model['id']}/evaluate",
        headers=auth_headers(token),
        json={"evaluation_dataset_id": evaluation_dataset["id"], "threshold_override": {}},
    )
    assert evaluate.status_code == 200

    time.sleep(0.1)
    evaluated = client.get(f"/api/v1/intent-libraries/{library['id']}", headers=auth_headers(token))
    assert evaluated.status_code == 200

    publish = client.post(
        f"/api/v1/models/{model['id']}/publish",
        headers=auth_headers(token),
        json={"note": "privacy ready"},
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


def test_build_database_connect_args_includes_tls_when_enabled():
    from app.db import build_database_connect_args

    args = build_database_connect_args(
        os.environ["DATABASE_URL"],
        require_tls=True,
        tls_mode="require",
        tls_root_cert="/tmp/root-ca.pem",
    )
    assert args["sslmode"] == "require"
    assert args["sslrootcert"] == "/tmp/root-ca.pem"


def test_device_privacy_export_and_delete_require_second_confirmation(client: TestClient, admin_token: str):
    library = create_published_library(client, admin_token, "privacy_runtime_lib", "隐私运行库")
    profile = create_profile(client, admin_token, "隐私运行方案", [library["id"]])

    publish_profile = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/publish",
        headers=auth_headers(admin_token),
        json={},
    )
    assert publish_profile.status_code == 200

    runtime = client.post(
        "/api/v1/runtime/devices/device_privacy_a/messages",
        headers=auth_headers(admin_token),
        json={"text": "开始烹饪", "device_context": {"page": "cook", "cooking": True}},
    )
    assert runtime.status_code == 200

    exported = client.get(
        "/api/v1/privacy/devices/device_privacy_a/export",
        headers=auth_headers(admin_token),
    )
    assert exported.status_code == 200
    export_payload = exported.json()["data"]
    assert export_payload["device_id"] == "device_privacy_a"
    assert len(export_payload["request_logs"]) == 1
    assert len(export_payload["device_sessions"]) == 1

    confirmation = client.post(
        "/api/v1/privacy/devices/device_privacy_a/delete-request",
        headers=auth_headers(admin_token),
        json={"reason": "gdpr_cleanup"},
    )
    assert confirmation.status_code == 200
    confirmation_token = confirmation.json()["data"]["confirmation_token"]

    delete_response = client.request(
        "DELETE",
        "/api/v1/privacy/devices/device_privacy_a",
        headers=auth_headers(admin_token),
        json={"confirmation_token": confirmation_token},
    )
    assert delete_response.status_code == 200

    exported_after = client.get(
        "/api/v1/privacy/devices/device_privacy_a/export",
        headers=auth_headers(admin_token),
    )
    assert exported_after.status_code == 404


def test_sensitive_dialog_and_knowledge_payloads_are_encrypted_at_rest(client: TestClient, admin_token: str, app):
    library = create_published_library(client, admin_token, "privacy_manual_lib", "隐私手测库")
    profile = create_profile(client, admin_token, "隐私手测方案", [library["id"]])

    session_response = client.post(
        f"/api/v1/dialog-profiles/{profile['id']}/test-sessions",
        headers=auth_headers(admin_token),
        json={"name": "隐私会话", "device_context": {"device_id": "privacy_device"}},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["session"]["id"]

    send_message = client.post(
        f"/api/v1/test-sessions/{session_id}/messages",
        headers=auth_headers(admin_token),
        json={"text": "这是需要加密的对话内容", "device_context": {"device_id": "privacy_device"}},
    )
    assert send_message.status_code == 200

    category = client.post(
        "/api/v1/knowledge-bases/categories",
        headers=auth_headers(admin_token),
        json={"name": "隐私文档", "icon": "📚", "description": "隐私测试"},
    )
    assert category.status_code == 200
    category_id = category.json()["data"]["category"]["id"]

    upload = client.post(
        f"/api/v1/knowledge-bases/{category_id}/documents/upload",
        headers=auth_headers(admin_token),
        json={
            "name": "隐私文档.md",
            "format": "markdown",
            "content": "# 标题\n这是需要加密的知识库原文。",
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["data"]["document"]["id"]

    with app.state.session_factory() as session:
        message_row = session.execute(
            select(models.TestSessionMessage).order_by(models.TestSessionMessage.created_at.desc())
        ).scalars().first()
        document_row = session.get(models.KnowledgeDocument, document_id)
        assert "这是需要加密的对话内容" not in message_row.text
        assert "这是需要加密的知识库原文" not in document_row.source_text
