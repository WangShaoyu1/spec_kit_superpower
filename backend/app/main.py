import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.batch_test import router as batch_test_router
from app.api.dialog_profile import router as dialog_profile_router
from app.api.health import router as health_router
from app.api.intent_library import router as intent_library_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.monitoring import router as monitoring_router
from app.api.privacy import router as privacy_router
from app.api.runtime import router as runtime_router
from app.api.user_mgmt import router as user_mgmt_router
from app.config import build_settings
from app.db import Base, build_database_connect_args, build_session_factory
from app.dependencies import ApiError, response_envelope
from app.seed import seed_database

logger = logging.getLogger(__name__)

# 白名单模式下的本机开发源（任意端口）；与 allow_origins 取并集，避免 .env 漏写字典端口
_LOCAL_DEV_ORIGIN_REGEX = r"^https?://(\[::1\]|localhost|127\.0\.0\.1)(:\d+)?$"


def create_app(overrides: dict[str, Any] | None = None) -> FastAPI:
    settings = build_settings(overrides)
    app = FastAPI(title=settings.app_name)

    database_connect_args = build_database_connect_args(
        settings.database_url,
        require_tls=settings.database_require_tls,
        tls_mode=settings.database_tls_mode,
        tls_root_cert=settings.database_tls_root_cert,
    )
    engine, session_factory = build_session_factory(settings.database_url, connect_args=database_connect_args)
    Base.metadata.create_all(engine)
    with session_factory() as session:
        seed_database(session, settings)

    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.database_connect_args = database_connect_args

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        return await call_next(request)

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return response_envelope(
            request,
            data=None,
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return response_envelope(
            request,
            data={"issues": exc.errors()},
            code="COMMON-422-VALIDATION",
            message="请求参数校验失败",
            status_code=422,
        )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(user_mgmt_router, prefix="/api/v1")
    app.include_router(intent_library_router, prefix="/api/v1")
    app.include_router(knowledge_base_router, prefix="/api/v1")
    app.include_router(dialog_profile_router, prefix="/api/v1")
    app.include_router(batch_test_router, prefix="/api/v1")
    app.include_router(monitoring_router, prefix="/api/v1")
    app.include_router(privacy_router, prefix="/api/v1")
    app.include_router(runtime_router, prefix="/api/v1")

    _api_route_count = sum(
        1 for r in app.routes if getattr(r, "path", None) and str(r.path).startswith("/api/")
    )
    logger.info("Mounted %d /api routes (e.g. knowledge-bases & intent-libraries present in OpenAPI)", _api_route_count)

    # 最后注册 CORS，保证作为最外层中间件处理预检并统一补上响应头
    if settings.cors_allow_all:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS: allow_all=True (Access-Control-Allow-Origin: *)")
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_origin_regex=_LOCAL_DEV_ORIGIN_REGEX,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(
            "CORS: allow_all=False origins=%s + localhost regex",
            settings.cors_allow_origins,
        )

    return app


# uvicorn app.main:app — 模块导入即挂载全部路由；/docs 与业务 API 始终同一套 OpenAPI。
# pytest 在 conftest 中将 DATABASE_URL 指向独立 PG 测试库（默认 smartchef_test），勿与开发库混用。
app = create_app()


__all__ = ["app", "create_app", "seed_database"]
