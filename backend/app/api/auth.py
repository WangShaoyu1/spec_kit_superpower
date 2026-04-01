from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid

from app.dependencies import get_current_user, get_db, load_capabilities, response_envelope, serialize_user, utc_now
from app.dependencies import ApiError
from app.models import AuthSession, UserAccount
from app.security import verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_db)):
    user = session.execute(select(UserAccount).where(UserAccount.username == payload.username)).scalar_one_or_none()
    if user is None or user.status != "active" or not verify_password(payload.password, user.password_hash):
        raise ApiError(401, "AUTH-401", "用户名或密码错误")

    settings = request.app.state.settings
    user.last_login_at = utc_now()
    token = uuid.uuid4().hex
    session.add(
        AuthSession(
            token=token,
            user_id=user.id,
            token_version=user.token_version,
            expires_at=utc_now() + timedelta(minutes=settings.access_token_expire_minutes),
        )
    )
    session.commit()

    return response_envelope(
        request,
        data={
            "access_token": token,
            "user": serialize_user(user),
            "capabilities": load_capabilities(session, user.role_key),
        },
    )


@router.get("/me")
def me(request: Request, user: UserAccount = Depends(get_current_user), session: Session = Depends(get_db)):
    return response_envelope(
        request,
        data={
            "user": serialize_user(user),
            "capabilities": load_capabilities(session, user.role_key),
        },
    )
