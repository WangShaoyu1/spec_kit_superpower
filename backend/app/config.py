from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartChef Backend"
    app_env: str = "local"
    # 技术选型：仅 PostgreSQL（psycopg 驱动）。禁止使用 SQLite 等作为业务库。
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/smartchef"
    database_require_tls: bool = False
    database_tls_mode: str = "require"
    database_tls_root_cert: str | None = None
    # False：表结构仅由 Alembic 管理（验收/企业默认）。本地首次请执行 scripts/bootstrap_db.py 或 alembic upgrade head。
    # pytest 进程由 conftest 设 DATABASE_RUN_CREATE_ALL=true，在清库后仍用 ORM 同步空 schema。
    database_run_create_all: bool = False
    # True：CORS 允许任意 Origin（搭配 main 里 allow_credentials=False，与 Bearer 头兼容）。
    # 生产环境建议设为 false，并改用 cors_allow_origins 白名单。
    cors_allow_all: bool = True
    # 仅当 cors_allow_all=False 时交给 CORSMiddleware；为 True 时 main.py 使用 allow_origins=["*"]，不读本列表
    cors_allow_origins: list[str] = [
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "http://127.0.0.1:4175",
        "http://localhost:4175",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    seed_admin_password: str = "Abc12345"
    access_token_expire_minutes: int = 480
    data_encryption_key: str = "smartchef-dev-aes256-key"
    privacy_confirmation_ttl_seconds: int = 600

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, v: str) -> str:
        u = (v or "").strip()
        if not u.lower().startswith("postgresql"):
            raise ValueError(
                "database_url 必须为 PostgreSQL（例如 postgresql+psycopg://user:pass@host:5432/dbname），"
                "本项目不采用 SQLite 作为业务数据库。"
            )
        return u

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def build_settings(overrides: dict[str, Any] | None = None) -> Settings:
    settings = Settings()
    if overrides:
        settings = settings.model_copy(update=overrides)
    return settings
