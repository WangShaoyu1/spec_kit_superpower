from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy.engine import URL, make_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import build_settings


def render_url(url: URL) -> str:
    return url.render_as_string(hide_password=False)


def render_psycopg_url(url: URL) -> str:
    drivername = "postgresql"
    if "+" in url.drivername:
        drivername = url.drivername.split("+", 1)[0]
    return render_url(url.set(drivername=drivername))


def resolve_target_urls() -> tuple[URL, URL, URL]:
    settings = build_settings()
    app_url = make_url(os.environ.get("DATABASE_URL", settings.database_url))
    test_url_raw = os.environ.get("DATABASE_URL_TEST")
    if test_url_raw:
        test_url = make_url(test_url_raw)
    else:
        test_database = app_url.database if str(app_url.database).endswith("_test") else f"{app_url.database}_test"
        test_url = app_url.set(database=test_database)
    admin_database = os.environ.get("DATABASE_ADMIN_DB", "postgres")
    admin_url = app_url.set(database=admin_database)
    return app_url, test_url, admin_url


def ensure_database_exists(target_url: URL, admin_url: URL, *, reset: bool) -> None:
    database_name = target_url.database
    if not database_name:
        raise ValueError("DATABASE_URL 必须包含数据库名")

    with psycopg.connect(render_psycopg_url(admin_url), autocommit=True) as conn:
        with conn.cursor() as cursor:
            if reset:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                    """,
                    (database_name,),
                )
                cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name)))
                print(f"[db] dropped database: {database_name}")

            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            exists = cursor.fetchone() is not None
            if not exists:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
                print(f"[db] created database: {database_name}")
            else:
                print(f"[db] database already exists: {database_name}")


def upgrade_database(target_url: URL) -> None:
    alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", render_url(target_url))
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = render_url(target_url)
    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
    print(f"[db] migrated database to head: {target_url.database}")


def seed_baseline_data(target_url: URL) -> None:
    """写入内置角色、能力绑定与 admin（与 uvicorn 启动时 seed_database 一致）。

    仅跑 Alembic 不会执行 seed，故迁移后须调用本函数或至少启动一次后端。
    """
    from app.db import build_database_connect_args, build_session_factory
    from app.seed import seed_database

    url_str = render_url(target_url)
    base = build_settings()
    connect_args = build_database_connect_args(
        url_str,
        require_tls=base.database_require_tls,
        tls_mode=base.database_tls_mode,
        tls_root_cert=base.database_tls_root_cert,
    )
    engine, session_factory = build_session_factory(url_str, connect_args=connect_args)
    try:
        settings = build_settings({"database_url": url_str})
        with session_factory() as session:
            seed_database(session, settings)
        print(f"[db] seeded baseline data (roles/admin if missing): {target_url.database}")
    finally:
        engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create PostgreSQL databases and apply Alembic migrations.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate target databases before running migrations.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app_url, test_url, admin_url = resolve_target_urls()
    for target_url in (app_url, test_url):
        ensure_database_exists(target_url, admin_url, reset=args.reset)
        upgrade_database(target_url)
        seed_baseline_data(target_url)


if __name__ == "__main__":
    main()
