from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class SlotCreate(BaseModel):
    slot_key: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=64)
    entity_type: str = Field(..., min_length=1, max_length=64)
    is_required: bool = False
    prompt_text: str | None = None
    constraints: dict | None = None
    sort_order: int = 0


class SlotInfo(BaseModel):
    id: UUID
    slot_key: str
    display_name: str
    entity_type: str
    is_required: bool
    prompt_text: str | None
    constraints: dict | None
    sort_order: int

    model_config = {"from_attributes": True}


class SlotUpdate(BaseModel):
    display_name: str | None = None
    entity_type: str | None = None
    is_required: bool | None = None
    prompt_text: str | None = None
    constraints: dict | None = None
    sort_order: int | None = None


class TrainingDataCreate(BaseModel):
    text: str = Field(..., min_length=1)
    language: str = "zh"
    slot_annotations: dict | None = None


class TrainingDataInfo(BaseModel):
    id: UUID
    text: str
    language: str
    slot_annotations: dict | None
    is_auto_translated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class IntentCreate(BaseModel):
    intent_key: str = Field(..., min_length=1, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=128)
    category: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    slots: list[SlotCreate] = Field(default_factory=list)


class IntentInfo(BaseModel):
    id: UUID
    intent_key: str
    display_name: str
    category: str
    description: str | None
    is_active: bool
    slots: list[SlotInfo] = []
    training_data_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntentUpdate(BaseModel):
    display_name: str | None = None
    category: str | None = None
    description: str | None = None
    is_active: bool | None = None


class IntentListResponse(BaseModel):
    items: list[IntentInfo]
    total: int
