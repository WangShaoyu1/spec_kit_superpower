"""Pydantic schemas for auth & user management."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)


class RoleInfo(BaseModel):
    id: str
    name: str


class UserInfo(BaseModel):
    id: str
    username: str
    name: str
    role: RoleInfo
    capabilities: list[str]


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$")
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)
    role_id: str = Field(...)


class UpdateUserRequest(BaseModel):
    name: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern=r"^(active|disabled)$")


class ResetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=8)
