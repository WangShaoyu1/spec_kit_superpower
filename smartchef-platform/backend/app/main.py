import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_pgvector
from app.core.redis import close_redis

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pgvector()
    logger.info("SmartChef backend started")
    yield
    await close_redis()
    logger.info("SmartChef backend stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# --- Middleware (order matters: first added = outermost) ---

from app.core.input_validator import InputValidationMiddleware  # noqa: E402
from app.core.rate_limiter import RateLimitMiddleware  # noqa: E402

app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---

from app.api.v1.auth import router as auth_router  # noqa: E402
from app.api.v1.intents import router as intents_router  # noqa: E402
from app.api.v1.knowledge import router as knowledge_router  # noqa: E402
from app.api.v1.profiles import router as profiles_router  # noqa: E402
from app.api.v1.test import router as test_router  # noqa: E402
from app.api.v1.device import router as device_router  # noqa: E402
from app.api.v1.versions import router as versions_router  # noqa: E402
from app.api.v1.batch_test import router as batch_test_router  # noqa: E402
from app.api.v1.monitoring import router as monitoring_router  # noqa: E402
from app.api.v1.users import router as users_router  # noqa: E402
from app.api.v1.health import router as health_router  # noqa: E402
from app.api.v1.data_management import router as data_management_router  # noqa: E402
from app.api.v1.testing import router as testing_router  # noqa: E402

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(intents_router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_V1_PREFIX)
app.include_router(profiles_router, prefix=settings.API_V1_PREFIX)
app.include_router(test_router, prefix=settings.API_V1_PREFIX)
app.include_router(device_router, prefix=settings.API_V1_PREFIX)
app.include_router(versions_router, prefix=settings.API_V1_PREFIX)
app.include_router(batch_test_router, prefix=settings.API_V1_PREFIX)
app.include_router(monitoring_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(data_management_router, prefix=settings.API_V1_PREFIX)
app.include_router(testing_router, prefix=settings.API_V1_PREFIX)
