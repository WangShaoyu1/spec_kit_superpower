import json
import secrets
from datetime import datetime
from typing import Any

from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.constants import ROLE_LABELS
from app.models import AuditLog, AuthSession, RoleCapabilityBinding, UserAccount


http_bearer = HTTPBearer(auto_error=False)


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def utc_now() -> datetime:
    return datetime.utcnow()


def iso_now() -> str:
    return utc_now().isoformat() + "Z"


def serialize_database_target(database_url: str) -> dict[str, Any]:
    url = make_url(database_url)
    return {
        "driver": url.drivername,
        "host": url.host,
        "port": url.port,
        "database": url.database,
    }


def response_envelope(
    request: Request,
    data: Any,
    code: str = "000000",
    message: str = "success",
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": data,
            "request_id": request.state.request_id,
            "timestamp": iso_now(),
        },
    )


def get_db(request: Request):
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def serialize_user(user: UserAccount) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.display_name,
        "role": user.role_key,
        "status": user.status,
        "created_at": user.created_at.strftime("%Y-%m-%d"),
        "last_login_at": user.last_login_at.isoformat().replace("+00:00", "Z") if user.last_login_at else None,
    }


def build_summary(users: list[UserAccount]) -> dict[str, int]:
    return {
        "total": len(users),
        "admin_count": sum(1 for user in users if user.role_key == "admin"),
        "pm_count": sum(1 for user in users if user.role_key == "pm"),
        "tester_count": sum(1 for user in users if user.role_key == "tester"),
    }


def load_capabilities(session: Session, role_key: str) -> list[str]:
    rows = session.execute(
        select(RoleCapabilityBinding.capability_key).where(RoleCapabilityBinding.role_key == role_key)
    ).all()
    return sorted(item[0] for item in rows)


def ensure_role_exists(role_key: str):
    if role_key not in ROLE_LABELS:
        raise ApiError(422, "USER-422-ROLE", "角色值不合法")


def ensure_status_exists(status: str):
    if status not in {"active", "disabled"}:
        raise ApiError(422, "USER-422-STATUS", "状态值不合法")


def create_audit_log(session: Session, actor_user_id: str, target_user_id: str, action: str, payload: dict[str, Any]):
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=action,
            payload=json.dumps(payload, ensure_ascii=False),
        )
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    session: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None:
        raise ApiError(401, "AUTH-401", "未登录或会话已失效")

    auth_session = session.get(AuthSession, credentials.credentials)
    if auth_session is None or auth_session.expires_at < utc_now():
        raise ApiError(401, "AUTH-401", "未登录或会话已失效")

    user = session.get(UserAccount, auth_session.user_id)
    if user is None or user.status != "active" or user.token_version != auth_session.token_version:
        raise ApiError(401, "AUTH-401", "未登录或会话已失效")

    request.state.current_user = user
    return user


def require_capability(capability_key: str):
    def dependency(
        request: Request,
        user: UserAccount = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) -> UserAccount:
        if capability_key not in load_capabilities(session, user.role_key):
            raise ApiError(403, "AUTH-403", "缺少目标能力点")
        request.state.current_user = user
        return user

    return dependency


def next_user_id(session: Session) -> str:
    count = session.execute(select(func.count()).select_from(UserAccount)).scalar_one()
    return f"user_{count + 1:03d}"


def generate_temporary_password() -> str:
    return secrets.token_urlsafe(12)
