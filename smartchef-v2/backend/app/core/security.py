"""T015 + T017: Security module — JWT, password hashing, RBAC middleware (dd-user-mgmt.md §5)."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
from jose import JWTError, jwt

from app.core.api_response import AuthException, BusinessException
from app.core.config import get_settings

# ---------------------------------------------------------------------------
# T015: Password hashing (dd-user-mgmt.md §5.3)
# ---------------------------------------------------------------------------

_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d).{8,}$")


def validate_password_strength(password: str) -> None:
    if not _PASSWORD_PATTERN.match(password):
        raise BusinessException("E10205", "密码至少 8 位，需包含字母和数字", http_status=422)


def hash_password(plain_password: str) -> str:
    validate_password_strength(plain_password)
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.PASSWORD_BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


# ---------------------------------------------------------------------------
# T015: JWT generation / verification (dd-user-mgmt.md §5.1, §5.2)
# ---------------------------------------------------------------------------


def generate_tokens(user, permissions) -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())

    access_payload = {
        "sub": str(user.id),
        "jti": access_jti,
        "role_id": str(user.role_id),
        "capabilities": [p.key for p in permissions],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    refresh_payload = {
        "sub": str(user.id),
        "jti": refresh_jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def is_token_blacklisted(jti: str) -> bool:
    from app.core.redis import get_redis
    try:
        redis = get_redis()
        return await redis.exists(f"token:blacklist:{jti}") > 0
    except RuntimeError:
        return False


async def blacklist_token(jti: str, ttl_seconds: int | None = None) -> None:
    from app.core.redis import get_redis
    settings = get_settings()
    redis = get_redis()
    if ttl_seconds is None:
        ttl_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await redis.setex(f"token:blacklist:{jti}", ttl_seconds, "1")


async def verify_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_sub": True, "require_exp": True},
        )
    except JWTError as e:
        if "expired" in str(e).lower():
            raise AuthException("E10104", "Token 已过期，请重新登录", http_status=401)
        raise AuthException("E10105", "Token 无效", http_status=401)

    if payload.get("type") != "access":
        raise AuthException("E10105", "Token 无效", http_status=401)

    required = {"sub", "jti", "role_id", "capabilities"}
    if not required.issubset(payload.keys()):
        raise AuthException("E10105", "Token 无效", http_status=401)

    if await is_token_blacklisted(payload["jti"]):
        raise AuthException("E10106", "Token 已注销", http_status=401)

    return payload


def verify_refresh_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_sub": True, "require_exp": True},
        )
    except JWTError as e:
        if "expired" in str(e).lower():
            raise AuthException("E10104", "Token 已过期，请重新登录", http_status=401)
        raise AuthException("E10105", "Token 无效", http_status=401)

    if payload.get("type") != "refresh":
        raise AuthException("E10105", "Token 无效", http_status=401)

    return payload


# ---------------------------------------------------------------------------
# Helper: extract bearer token
# ---------------------------------------------------------------------------


def extract_bearer_token(request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth[7:]


# ---------------------------------------------------------------------------
# T017: RBAC middleware (dd-user-mgmt.md §5.6)
# ---------------------------------------------------------------------------


@dataclass
class CurrentUser:
    user_id: str
    role_id: str
    capabilities: list[str] = field(default_factory=list)


def require_capability(*capability_keys: str, require_all: bool = True):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or (args[0] if args else None)
            if request is None:
                raise AuthException("E10102", "请先登录", http_status=401)

            token = extract_bearer_token(request)
            if not token:
                raise AuthException("E10102", "请先登录", http_status=401)

            payload = await verify_access_token(token)

            user_caps = set(payload.get("capabilities", []))
            required = set(capability_keys)

            if require_all:
                if not required.issubset(user_caps):
                    raise AuthException("E10107", "无权限执行此操作", http_status=403)
            else:
                if not required & user_caps:
                    raise AuthException("E10107", "无权限执行此操作", http_status=403)

            request.state.current_user = CurrentUser(
                user_id=payload["sub"],
                role_id=payload["role_id"],
                capabilities=payload["capabilities"],
            )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def get_current_user_from_token(request) -> CurrentUser:
    token = extract_bearer_token(request)
    if not token:
        raise AuthException("E10102", "请先登录", http_status=401)
    payload = await verify_access_token(token)
    return CurrentUser(
        user_id=payload["sub"],
        role_id=payload["role_id"],
        capabilities=payload["capabilities"],
    )
