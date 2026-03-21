"""Pydantic schemas for Dialog Profile module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# DialogProfile
# ---------------------------------------------------------------------------

class CreateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    command_threshold: float = Field(0.7, ge=0.0, le=1.0)
    route_strategy: str = Field("intent_first", pattern=r"^(intent_first|knowledge_first|auto)$")
    llm_provider: str | None = Field(None, max_length=64)
    llm_model: str | None = Field(None, max_length=64)
    session_timeout_min: int = Field(10, ge=1, le=1440)


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    command_threshold: float | None = Field(None, ge=0.0, le=1.0)
    route_strategy: str | None = Field(None, pattern=r"^(intent_first|knowledge_first|auto)$")
    llm_provider: str | None = Field(None, max_length=64)
    llm_model: str | None = Field(None, max_length=64)
    session_timeout_min: int | None = Field(None, ge=1, le=1440)


# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

class CreatePersonaRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1, max_length=10000)
    personality: str | None = Field(None, max_length=500)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=1, le=8192)


class UpdatePersonaRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    system_prompt: str | None = Field(None, min_length=1, max_length=10000)
    personality: str | None = Field(None, max_length=500)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=8192)


# ---------------------------------------------------------------------------
# ProfileLibraryBinding
# ---------------------------------------------------------------------------

class BindLibraryRequest(BaseModel):
    library_id: UUID
    priority: int = Field(0, ge=0)
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)


class UpdateBindingsRequest(BaseModel):
    bindings: list[BindLibraryRequest]


# ---------------------------------------------------------------------------
# PublishedVersion
# ---------------------------------------------------------------------------

class PublishRequest(BaseModel):
    pass


# ---------------------------------------------------------------------------
# Test Session / Message
# ---------------------------------------------------------------------------

class CreateTestSessionRequest(BaseModel):
    name: str = Field("未命名会话", min_length=1, max_length=128)


class UpdateTestSessionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class SendTestMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
