from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class PersonaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    personality: str = Field(..., min_length=1)
    tone_style: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)


class PersonaInfo(BaseModel):
    id: UUID
    name: str
    personality: str
    tone_style: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonaUpdate(BaseModel):
    name: str | None = None
    personality: str | None = None
    tone_style: str | None = None
    system_prompt: str | None = None


class DialogProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    llm_provider: str = Field(..., min_length=1, max_length=64)
    llm_config: dict = Field(default_factory=dict)
    persona_id: UUID | None = None
    routing_strategy: str = "command_first"
    session_timeout_minutes: int = 10
    intent_ids: list[UUID] | None = None
    knowledge_base_ids: list[UUID] | None = None


class DialogProfileInfo(BaseModel):
    id: UUID
    name: str
    description: str | None
    llm_provider: str
    llm_config: dict
    persona_id: UUID | None
    persona: PersonaInfo | None = None
    routing_strategy: str
    session_timeout_minutes: int
    intent_ids: list[UUID] | None
    knowledge_base_ids: list[UUID] | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DialogProfileUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    llm_provider: str | None = None
    llm_config: dict | None = None
    persona_id: UUID | None = None
    routing_strategy: str | None = None
    session_timeout_minutes: int | None = None
    intent_ids: list[UUID] | None = None
    knowledge_base_ids: list[UUID] | None = None
    status: str | None = None
