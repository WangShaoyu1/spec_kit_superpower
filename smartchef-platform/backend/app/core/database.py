from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_pgvector():
    try:
        async with engine.begin() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
            )
    except Exception as e:
        err_msg = str(e)
        is_refused = (
            isinstance(e, OSError) and getattr(e, "winerror", None) == 10061
        ) or (getattr(e, "args", None) and "10061" in str(e.args)) or "Connect call failed" in err_msg or "connection refused" in err_msg.lower()
        if is_refused:
            raise RuntimeError(
                "PostgreSQL is not running or not reachable at localhost:5432. "
                "Start the database (e.g. run: python scripts/manage_services.py start from repo root, or start PostgreSQL service) and try again."
            ) from e
        raise
