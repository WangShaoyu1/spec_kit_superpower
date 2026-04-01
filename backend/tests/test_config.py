from contextlib import contextmanager

from sqlalchemy import func, select, text

from app.config import build_settings
from app.db import Base, build_session_factory
from app.main import create_app, seed_database
from app.models import CapabilityDefinition, RoleCapabilityBinding, RoleDefinition, UserAccount


def test_default_database_url_matches_local_postgres_bootstrap(monkeypatch):
    # 校验未设置 DATABASE_URL 时 Settings 类字段默认值（与 conftest 注入的环境无关）
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = build_settings()

    assert settings.database_url == "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smartchef_v2"


def test_seed_database_succeeds_on_local_postgres_bootstrap():
    database_url = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smartchef_v2_test"
    engine, session_factory = build_session_factory(database_url)

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    Base.metadata.create_all(engine)

    try:
        with session_factory() as session:
            seed_database(session, build_settings({"database_url": database_url}))

        with session_factory() as session:
            assert session.execute(select(func.count()).select_from(RoleDefinition)).scalar_one() == 3
            assert session.execute(select(func.count()).select_from(CapabilityDefinition)).scalar_one() > 0
            assert session.execute(select(func.count()).select_from(RoleCapabilityBinding)).scalar_one() > 0
            assert session.execute(select(func.count()).select_from(UserAccount)).scalar_one() == 1
    finally:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))


def test_create_app_skips_create_all_when_database_run_create_all_disabled(monkeypatch):
    calls: list[object] = []
    fake_engine = object()

    @contextmanager
    def fake_session_factory():
        yield object()

    monkeypatch.setattr("app.main.build_session_factory", lambda *_args, **_kwargs: (fake_engine, fake_session_factory))
    monkeypatch.setattr("app.main.seed_database", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(Base.metadata, "create_all", lambda engine: calls.append(engine))

    create_app(
        {
            "app_env": "local",
            "database_url": "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smartchef_v2",
            "database_run_create_all": False,
        }
    )

    assert calls == []


def test_create_app_runs_create_all_when_database_run_create_all_enabled(monkeypatch):
    calls: list[object] = []
    fake_engine = object()

    @contextmanager
    def fake_session_factory():
        yield object()

    monkeypatch.setattr("app.main.build_session_factory", lambda *_args, **_kwargs: (fake_engine, fake_session_factory))
    monkeypatch.setattr("app.main.seed_database", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(Base.metadata, "create_all", lambda engine: calls.append(engine))

    create_app(
        {
            "app_env": "test",
            "database_url": "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smartchef_v2_test",
            "database_run_create_all": True,
        }
    )

    assert calls == [fake_engine]
