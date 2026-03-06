from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartChef Dialog Management Platform"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smartchef"
    REDIS_URL: str = "redis://localhost:6379/0"

    ZENMUX_API_KEY: str = ""
    ZENMUX_BASE_URL: str = "https://zenmux.ai/api/v1"
    BRAVE_SEARCH_API_KEY: str = ""

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123456"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
