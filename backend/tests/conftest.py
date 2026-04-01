import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

# 须先于 `import app.main`：main 末尾会 `app = create_app()`，pytest 进程必须指向独立测试库。
if "pytest" in sys.modules:
    from tests.constants import get_pytest_database_url

    os.environ["DATABASE_URL"] = get_pytest_database_url()
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("DATABASE_RUN_CREATE_ALL", "true")

from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_postgres_public_schema():
    """每个用例前重建 public schema，避免共享 smartchef_v2_test 时数据与唯一键冲突。"""
    url = os.environ["DATABASE_URL"]
    if not url.startswith("postgresql"):
        yield
        return
    engine = create_engine(url, future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    yield


@pytest.fixture
def app():
    return create_app(
        {
            "app_env": "test",
            "database_url": os.environ["DATABASE_URL"],
            "database_run_create_all": True,
            "seed_admin_password": "Abc12345",
        }
    )


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Abc12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]
