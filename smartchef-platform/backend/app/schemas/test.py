from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TestSessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    profile_id: UUID
    device_context: dict | None = None
    notes: str | None = None


class TestSessionInfo(BaseModel):
    id: UUID
    name: str
    profile_id: UUID
    device_context: dict | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TestChatRequest(BaseModel):
    session_id: UUID
    text: str = Field(..., min_length=1)


class TestChatResponse(BaseModel):
    domain: str
    route_confidence: float
    intent: str | None = None
    intent_confidence: float | None = None
    slots: dict = {}
    response_text: str
    needs_followup: bool = False
    language: str = "zh"
    latency_ms: int = 0
    debug_info: dict = {}
