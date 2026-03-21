import logging
import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartChef Dialog Management Platform"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database (PostgreSQL 16 + asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/smartchef_v2"

    # Redis 7.x
    REDIS_URL: str = "redis://127.0.0.1:6379/1"

    # JWT (dd-user-mgmt.md §8.1)
    SECRET_KEY: str = "change-me-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Admin seed (dd-global.md §7)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123456"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting (dd-user-mgmt.md §5.5)
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    LOGIN_RATE_PER_MINUTE: int = 5

    # Input validation (ad-global.md §6.1)
    INPUT_MAX_LENGTH: int = 2048

    # Password (dd-user-mgmt.md §5.3)
    PASSWORD_BCRYPT_ROUNDS: int = 12

    # LLM（ZenMux 统一网关，与 smartchef-platform 一致）
    ZENMUX_API_KEY: str = ""
    ZENMUX_BASE_URL: str = "https://zenmux.ai/api/v1"

    # 联网搜索（Brave Search，闲聊/知识未命中时可选）
    BRAVE_SEARCH_API_KEY: str = ""

    # Device API key (empty = no key required, for dev only)
    DEVICE_API_KEY: str = ""

    # ONNX / Training artifacts base directory (relative to backend root)
    ONNX_MODEL_PATH: str = "models/intent_model.onnx"
    MODEL_DATA_DIR: str = ""

    # HuggingFace：留空则使用 <backend>/data/hf_cache；同一 base 模型只下载一次后本地复用
    HF_HOME: str = ""

    # Pipeline
    PIPELINE_CHAT_TIMEOUT_SECONDS: int = 15

    # Logging (dd-monitoring.md)
    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def _backend_root():
    from pathlib import Path
    return Path(__file__).resolve().parents[2]


def resolve_artifact_path(artifact_uri: str | None) -> str | None:
    """Resolve a relative artifact_uri (e.g. 'data/models/…/model.onnx') to an absolute path."""
    if not artifact_uri:
        return None
    from pathlib import Path
    p = Path(artifact_uri)
    if p.is_absolute():
        return str(p)
    settings = get_settings()
    base = Path(settings.MODEL_DATA_DIR) if settings.MODEL_DATA_DIR else _backend_root()
    return str(base / artifact_uri)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.SECRET_KEY == "change-me-in-production":
        if not settings.DEBUG:
            raise RuntimeError(
                "SECRET_KEY must be set to a strong random value in production. "
                "Set the SECRET_KEY environment variable."
            )
        warnings.warn(
            "Using default SECRET_KEY — acceptable for development only.",
            UserWarning,
            stacklevel=2,
        )
    return settings
