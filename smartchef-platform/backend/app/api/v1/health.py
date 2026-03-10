"""
健康检查端点
检查 PostgreSQL、Redis 等组件的连接状态与响应时间
"""
import time
from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis_client

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check(response: Response):
    """
    综合健康检查端点
    检查 PostgreSQL、Redis 连接状态，返回各组件的健康状态和响应时间。
    任一组件不可用时返回 503。
    """
    results = {}
    all_healthy = True

    # 检查 PostgreSQL 连接
    db_start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ms = round((time.perf_counter() - db_start) * 1000, 2)
        results["database"] = {"status": "healthy", "response_ms": db_ms}
    except Exception as e:
        db_ms = round((time.perf_counter() - db_start) * 1000, 2)
        results["database"] = {
            "status": "unhealthy",
            "response_ms": db_ms,
            "error": str(e),
        }
        all_healthy = False

    # 检查 Redis 连接
    redis_start = time.perf_counter()
    try:
        await redis_client.ping()
        redis_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        results["redis"] = {"status": "healthy", "response_ms": redis_ms}
    except Exception as e:
        redis_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        results["redis"] = {
            "status": "unhealthy",
            "response_ms": redis_ms,
            "error": str(e),
        }
        all_healthy = False

    if not all_healthy:
        response.status_code = 503

    return {"status": "healthy" if all_healthy else "degraded", "components": results}
