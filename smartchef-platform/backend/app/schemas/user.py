from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=1, max_length=64)
    role_id: UUID | None = None


class UserInfo(BaseModel):
    id: UUID
    username: str
    display_name: str
    role_id: UUID | None
    role_name: str | None = None
    permissions: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = None
    role_id: UUID | None = None
    is_active: bool | None = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    permissions: dict = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    permissions: dict | None = None


class RoleInfo(BaseModel):
    id: UUID
    name: str
    permissions: dict
    is_system: bool

    model_config = {"from_attributes": True}
