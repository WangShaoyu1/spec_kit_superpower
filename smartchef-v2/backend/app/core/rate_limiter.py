"""T022: Login rate limiter (dd-user-mgmt.md §5.5)."""

import logging

from app.core.api_response import AuthException, BusinessException
from app.core.config import get_settings
from app.core.redis import get_redis

logger = logging.getLogger("smartchef.rate_limiter")


async def check_login_rate_limit(ip: str, username: str) -> None:
    settings = get_settings()
    try:
        redis = get_redis()
    except RuntimeError:
        logger.warning("Redis unavailable, skipping rate limit check")
        return

    ip_key = f"login_rate:{ip}"
    count = await redis.incr(ip_key)
    if count == 1:
        await redis.expire(ip_key, 60)
    if count > settings.LOGIN_RATE_PER_MINUTE:
        raise BusinessException("E00004", "请求过于频繁，请稍后再试", http_status=429)

    lockout_key = f"login_lockout:{username}"
    if await redis.exists(lockout_key):
        ttl = await redis.ttl(lockout_key)
        raise AuthException("E10108", f"登录失败次数过多，请 {ttl // 60 + 1} 分钟后再试", http_status=429)


async def record_login_failure(username: str) -> None:
    settings = get_settings()
    try:
        redis = get_redis()
    except RuntimeError:
        return

    fail_key = f"login_fail:{username}"
    count = await redis.incr(fail_key)
    if count == 1:
        await redis.expire(fail_key, settings.LOGIN_LOCKOUT_MINUTES * 60)
    if count >= settings.LOGIN_MAX_ATTEMPTS:
        await redis.setex(f"login_lockout:{username}", settings.LOGIN_LOCKOUT_MINUTES * 60, "1")


async def clear_login_failures(username: str) -> None:
    try:
        redis = get_redis()
    except RuntimeError:
        return
    await redis.delete(f"login_fail:{username}", f"login_lockout:{username}")
