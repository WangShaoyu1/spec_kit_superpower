"""FastAPI application entry point with full middleware stack."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.api_response import BusinessException, business_exception_handler
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    from app.core.database import init_db
    from app.core.redis import init_redis

    await init_db()
    await init_redis()
    yield
    from app.core.database import close_db
    from app.core.redis import close_redis

    await close_db()
    await close_redis()


def create_app() -> FastAPI:
    from app.core.hf_cache import configure_huggingface_cache

    configure_huggingface_cache()
    settings = get_settings()

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Exception handlers
    application.add_exception_handler(BusinessException, business_exception_handler)

    # Middleware stack (order: last added = first executed)
    # Request → CORS → Logging → InputValidation → Route Handler
    from app.core.input_validator import InputValidationMiddleware
    from app.core.logging_middleware import LoggingMiddleware

    application.add_middleware(InputValidationMiddleware)
    application.add_middleware(LoggingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routers(application, settings)

    return application


def _register_routers(application: FastAPI, settings):
    from app.api.v1.auth import router as auth_router
    from app.api.v1.datasets import router as datasets_router
    from app.api.v1.health import router as health_router
    from app.api.v1.intent_libraries import router as intent_libraries_router
    from app.api.v1.intent_testing import router as intent_testing_router
    from app.api.v1.intents import router as intents_router
    from app.api.v1.model_versions import router as model_versions_router
    from app.api.v1.permissions import router as permissions_router
    from app.api.v1.roles import router as roles_router
    from app.api.v1.users import router as users_router
    from app.api.v1.knowledge import router as knowledge_router

    application.include_router(health_router, prefix=settings.API_V1_PREFIX, tags=["health"])
    application.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    application.include_router(intent_libraries_router, prefix=settings.API_V1_PREFIX)
    application.include_router(model_versions_router, prefix=settings.API_V1_PREFIX)
    application.include_router(datasets_router, prefix=settings.API_V1_PREFIX)
    application.include_router(intents_router, prefix=settings.API_V1_PREFIX)
    application.include_router(intent_testing_router, prefix=settings.API_V1_PREFIX)

    from app.api.v1.profiles import router as profiles_router
    from app.api.v1.versions import router as versions_router
    from app.api.v1.testing import router as testing_router

    application.include_router(profiles_router, prefix=settings.API_V1_PREFIX)
    application.include_router(versions_router, prefix=settings.API_V1_PREFIX)
    application.include_router(testing_router, prefix=settings.API_V1_PREFIX)
    application.include_router(users_router, prefix=settings.API_V1_PREFIX)
    application.include_router(roles_router, prefix=settings.API_V1_PREFIX)
    application.include_router(permissions_router, prefix=settings.API_V1_PREFIX)
    application.include_router(knowledge_router, prefix=settings.API_V1_PREFIX)

    from app.api.v1.monitoring import router as monitoring_router

    application.include_router(monitoring_router, prefix=settings.API_V1_PREFIX)

    from app.api.v1.batch_tests import router as batch_tests_router

    application.include_router(batch_tests_router, prefix=settings.API_V1_PREFIX)

    from app.api.v1.dialog import router as dialog_router

    application.include_router(dialog_router, prefix=settings.API_V1_PREFIX)


app = create_app()
