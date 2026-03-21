"""T018: Authentication API routes (dd-user-mgmt.md §9.1)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import AuthException, success_response
from app.core.database import get_db
from app.core.security import blacklist_token, extract_bearer_token, verify_access_token
from app.schemas.user import LoginRequest, LogoutRequest, RefreshRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    ip = _get_client_ip(request)
    data = await auth_service.login(db, body.username, body.password, ip)
    return success_response(data)


@router.post("/logout")
async def logout(request: Request, body: LogoutRequest | None = None):
    token = extract_bearer_token(request)
    if not token:
        raise AuthException("E10102", "请先登录", http_status=401)
    payload = await verify_access_token(token)
    await blacklist_token(payload["jti"])
    return success_response(None, msg="登出成功")


@router.get("/me")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    token = extract_bearer_token(request)
    if not token:
        raise AuthException("E10102", "请先登录", http_status=401)
    payload = await verify_access_token(token)
    data = await auth_service.get_current_user(db, payload)
    return success_response(data)


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = await auth_service.refresh_token(db, body.refresh_token)
    return success_response(data)
