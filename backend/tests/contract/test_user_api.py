from fastapi.testclient import TestClient


from sqlalchemy import select

from app.models import AuditLog


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_admin_capabilities(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Abc12345"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "success"
    assert payload["data"]["user"]["username"] == "admin"
    assert "user_manage" in payload["data"]["capabilities"]


def test_create_user_returns_directory_with_summary(client: TestClient, admin_token: str):
    create_response = client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": "wang_pm",
            "name": "小王",
            "password": "Abc12345",
            "role": "pm",
        },
    )

    assert create_response.status_code == 200

    list_response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
    )

    assert list_response.status_code == 200
    payload = list_response.json()["data"]
    assert any(item["username"] == "wang_pm" for item in payload["items"])
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["pm_count"] == 1


def test_create_user_writes_dotted_audit_event(client: TestClient, admin_token: str, app):
    create_response = client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": "audit_pm",
            "name": "审计小王",
            "password": "Abc12345",
            "role": "pm",
        },
    )

    assert create_response.status_code == 200

    with app.state.session_factory() as session:
        audit_log = session.execute(
            select(AuditLog).where(AuditLog.action == "user.created").order_by(AuditLog.id.desc())
        ).scalar_one()

    assert audit_log.target_user_id == create_response.json()["data"]["user"]["id"]
    assert '"role": "pm"' in audit_log.payload


def test_role_change_invalidates_existing_session(client: TestClient, admin_token: str):
    client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": "wang_pm",
            "name": "小王",
            "password": "Abc12345",
            "role": "pm",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "wang_pm", "password": "Abc12345"},
    )
    pm_token = login_response.json()["data"]["access_token"]

    list_response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
    )
    created_user = next(item for item in list_response.json()["data"]["items"] if item["username"] == "wang_pm")

    update_response = client.patch(
        f"/api/v1/admin/users/{created_user['id']}/role",
        headers=auth_headers(admin_token),
        json={"role": "tester"},
    )

    assert update_response.status_code == 200

    me_response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(pm_token),
    )

    assert me_response.status_code == 401
    assert me_response.json()["code"] == "AUTH-401"


def test_role_change_writes_dotted_audit_event(client: TestClient, admin_token: str, app):
    client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": "audit_tester",
            "name": "审计角色",
            "password": "Abc12345",
            "role": "pm",
        },
    )
    list_response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
    )
    created_user = next(item for item in list_response.json()["data"]["items"] if item["username"] == "audit_tester")

    update_response = client.patch(
        f"/api/v1/admin/users/{created_user['id']}/role",
        headers=auth_headers(admin_token),
        json={"role": "tester"},
    )

    assert update_response.status_code == 200

    with app.state.session_factory() as session:
        audit_log = session.execute(
            select(AuditLog).where(AuditLog.action == "user.role_changed").order_by(AuditLog.id.desc())
        ).scalar_one()

    assert audit_log.target_user_id == created_user["id"]
    assert '"before": "pm"' in audit_log.payload
    assert '"after": "tester"' in audit_log.payload


def test_builtin_admin_cannot_be_disabled(client: TestClient, admin_token: str):
    response = client.post(
        "/api/v1/admin/users/user_001/status",
        headers=auth_headers(admin_token),
        json={"status": "disabled"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "USER-409-BUILTIN-ADMIN"


def test_reset_password_does_not_expose_plaintext_secret(client: TestClient, admin_token: str, app):
    client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": "wang_pm",
            "name": "小王",
            "password": "Abc12345",
            "role": "pm",
        },
    )

    list_response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
    )
    created_user = next(item for item in list_response.json()["data"]["items"] if item["username"] == "wang_pm")

    reset_response = client.post(
        f"/api/v1/admin/users/{created_user['id']}/reset-password",
        headers=auth_headers(admin_token),
    )

    assert reset_response.status_code == 200
    payload = reset_response.json()["data"]
    assert payload == {
        "password_reset": True,
        "delivery": "out_of_band",
        "require_password_change": True,
    }

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "wang_pm", "password": "Abc12345"},
    )
    assert login_response.status_code == 401

    with app.state.session_factory() as session:
        audit_log = session.execute(
            select(AuditLog).where(AuditLog.action == "password_reset").order_by(AuditLog.id.desc())
        ).scalar_one()

    assert "temporary_password" not in audit_log.payload
    assert "Abc12345" not in audit_log.payload


def test_validation_error_uses_unified_response_envelope(client: TestClient, admin_token: str):
    response = client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": "xy",
            "name": "",
            "password": "short",
            "role": "pm",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "COMMON-422-VALIDATION"
    assert payload["message"] == "请求参数校验失败"
    assert payload["data"]["issues"]
    assert payload["request_id"]
    assert payload["timestamp"]
