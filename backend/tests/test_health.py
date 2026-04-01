import os

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_formal_backend_settings():
    database_url = os.environ["DATABASE_URL"]
    client = TestClient(create_app({"app_env": "test", "database_url": database_url}))

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "000000"
    assert payload["message"] == "success"
    assert payload["data"]["service"] == "SmartChef Backend"
    assert payload["data"]["environment"] == "test"
    assert "database_url" not in payload["data"]
    assert "postgresql" in payload["data"]["database"]["driver"]
    assert payload["data"]["database"]["database"] is not None
