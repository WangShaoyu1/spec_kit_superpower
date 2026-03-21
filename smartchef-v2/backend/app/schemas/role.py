"""Pydantic schemas for role CRUD and permission assignment."""

from pydantic import BaseModel, Field


class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    description: str | None = Field(None, max_length=200)
    permission_keys: list[str] = Field(default_factory=list)


class UpdateRoleRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=30)
    description: str | None = Field(None, max_length=200)


class UpdateRolePermissionsRequest(BaseModel):
    permission_keys: list[str] = Field(...)


class AssignRoleRequest(BaseModel):
    role_id: str = Field(...)
