import os

from fastapi.testclient import TestClient

from app.main import create_app


def test_login_preflight_allows_local_frontend_origin():
    client = TestClient(
        create_app(
            {
                "app_env": "test",
                "database_url": os.environ["DATABASE_URL"],
            }
        )
    )

    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    # 默认 cors_allow_all=True → Allow-Origin 为 *
    assert response.headers["access-control-allow-origin"] == "*"


def test_login_preflight_whitelist_allows_localhost_port():
    """cors_allow_all=False 时仍应通过本机正则放行任意端口（如 :4173）。"""
    client = TestClient(
        create_app(
            {
                "app_env": "test",
                "database_url": os.environ["DATABASE_URL"],
                "cors_allow_all": False,
                "cors_allow_origins": ["https://only.example.com"],
            }
        )
    )

    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4173"
