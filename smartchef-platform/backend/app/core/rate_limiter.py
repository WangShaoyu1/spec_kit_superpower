"""API 限流中间件 — 基于 Redis 滑动窗口的请求速率限制。

实现要点：
- 滑动窗口算法，以客户端 IP（或 API Key）为维度
- 默认 10 QPS（可通过 Settings.RATE_LIMIT_QPS 配置）
- 超限返回 429 Too Many Requests，响应头包含限流信息
- 健康检查等内部路径自动豁免
"""
import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

# 不受限流保护的路径前缀
_EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/api/v1/health")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于 Redis 滑动窗口的 API 限流中间件。"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        settings = get_settings()
        self.max_requests = settings.RATE_LIMIT_QPS
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
        self.enabled = settings.RATE_LIMIT_ENABLED

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not self.enabled:
            return await call_next(request)

        # 豁免路径
        path = request.url.path
        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        # 限流维度：优先使用 X-API-Key，否则使用客户端 IP
        client_id = request.headers.get("x-api-key") or _get_client_ip(request)
        allowed, remaining, retry_after = await _check_rate_limit(
            client_id, self.max_requests, self.window_seconds
        )

        if not allowed:
            logger.warning("限流触发: client=%s, path=%s", client_id, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests — 请求过于频繁，请稍后重试"},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def _get_client_ip(request: Request) -> str:
    """提取客户端真实 IP，支持反向代理的 X-Forwarded-For。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Redis 滑动窗口限流核心逻辑
# ---------------------------------------------------------------------------

# Lua 脚本：原子性地执行滑动窗口计数
# KEYS[1] = 限流 key
# ARGV[1] = 当前时间戳（微秒）
# ARGV[2] = 窗口大小（微秒）
# ARGV[3] = 最大请求数
# 返回: [allowed(0/1), remaining, retry_after_ms]
_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_req = tonumber(ARGV[3])

local window_start = now - window
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

local count = redis.call('ZCARD', key)

if count < max_req then
    redis.call('ZADD', key, now, now .. '-' .. math.random(1, 1000000))
    redis.call('PEXPIRE', key, math.ceil(window / 1000))
    return {1, max_req - count - 1, 0}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 0
    if #oldest >= 2 then
        retry_after = math.ceil((tonumber(oldest[2]) + window - now) / 1000000)
    end
    if retry_after < 1 then retry_after = 1 end
    return {0, 0, retry_after}
end
"""


async def _check_rate_limit(
    client_id: str, max_requests: int, window_seconds: int
) -> tuple[bool, int, int]:
    """执行滑动窗口限流检查。

    Returns:
        (allowed, remaining, retry_after_seconds)
    """
    key = f"ratelimit:{client_id}"
    now_us = int(time.time() * 1_000_000)
    window_us = window_seconds * 1_000_000

    try:
        result = await redis_client.eval(
            _SLIDING_WINDOW_LUA, 1, key, now_us, window_us, max_requests
        )
        allowed = bool(result[0])
        remaining = int(result[1])
        retry_after = int(result[2])
        return allowed, remaining, retry_after
    except Exception:
        # Redis 不可用时放行请求（fail-open 策略）
        logger.exception("限流 Redis 调用失败，放行请求")
        return True, max_requests, 0
