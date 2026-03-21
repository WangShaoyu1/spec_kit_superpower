import redis.asyncio as aioredis

from app.core.config import get_settings

redis_client: aioredis.Redis | None = None


async def init_redis():
    global redis_client
    settings = get_settings()
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
    )
    await redis_client.ping()


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()


def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client
