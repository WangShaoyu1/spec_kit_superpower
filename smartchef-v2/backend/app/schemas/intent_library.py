"""Pydantic schemas for Intent Library module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# IntentLibrary
# ---------------------------------------------------------------------------

class CreateLibraryRequest(BaseModel):
    library_key: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(..., min_length=2, max_length=8)
    description: str | None = Field(None, max_length=500)
    default_confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    default_intent_f1_threshold: float = Field(0.95, ge=0.0, le=1.0)
    default_slot_f1_threshold: float = Field(0.90, ge=0.0, le=1.0)


class UpdateLibraryRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    language: str | None = Field(None, min_length=2, max_length=8)  # D022: 支持更新语言，与 CreateLibraryRequest 一致
    description: str | None = Field(None, max_length=500)
    default_confidence_threshold: float | None = Field(None, ge=0.0, le=1.0)
    default_intent_f1_threshold: float | None = Field(None, ge=0.0, le=1.0)
    default_slot_f1_threshold: float | None = Field(None, ge=0.0, le=1.0)


class LibraryResponse(BaseModel):
    id: UUID
    library_key: str
    name: str
    language: str
    description: str | None
    default_confidence_threshold: float
    default_intent_f1_threshold: float
    default_slot_f1_threshold: float
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    model_count: int | None = None
    latest_model_status: str | None = None


# ---------------------------------------------------------------------------
# ModelVersion
# ---------------------------------------------------------------------------

class CreateModelRequest(BaseModel):
    version_name: str = Field(..., min_length=1, max_length=128)
    train_dataset_id: UUID | None = None
    train_config: dict = Field(default_factory=dict)
    notes: str | None = None


class ModelVersionResponse(BaseModel):
    id: UUID
    library_id: UUID
    version_name: str
    status: str
    train_dataset_id: UUID | None
    train_dataset_name: str | None = None
    dataset_name: str | None = None
    train_config: dict
    metrics: dict
    artifact_type: str | None
    artifact_uri: str | None
    package_uri: str | None
    notes: str | None
    is_testable: bool
    is_published: bool
    progress: int
    published_at: datetime | None
    trained_at: datetime | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class StartTrainingRequest(BaseModel):
    """Optional hyperparameters merged into model.train_config for auditing / future trainer."""

    base_model: str | None = Field(None, max_length=128)
    learning_rate: float | None = Field(None, gt=0)
    batch_size: int | None = Field(None, ge=1)
    epochs: int | None = Field(None, ge=1)
    early_stopping: bool | None = None
    early_stopping_patience: int | None = Field(None, ge=1)


class CompleteTrainingRequest(BaseModel):
    metrics: dict = Field(default_factory=dict)


class StartEvaluationRequest(BaseModel):
    dataset_id: UUID
    threshold_intent_f1: float | None = Field(None, ge=0.0, le=1.0)
    threshold_slot_f1: float | None = Field(None, ge=0.0, le=1.0)


class EvaluationResponse(BaseModel):
    id: UUID
    library_id: UUID
    model_version_id: UUID
    dataset_id: UUID
    status: str
    threshold_intent_f1: float
    threshold_slot_f1: float
    result_summary: dict
    analysis: dict
    total_samples: int
    completed_samples: int
    started_at: datetime | None
    completed_at: datetime | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Dataset (Training + Evaluation)
# ---------------------------------------------------------------------------

class CreateDatasetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)
    source_type: str = Field("manual", max_length=16)
    config: dict = Field(default_factory=dict)


class UpdateDatasetRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)
    config: dict | None = None


class DatasetResponse(BaseModel):
    id: UUID
    library_id: UUID
    name: str
    description: str | None
    source_type: str
    schema_version: str
    sample_count: int
    intent_count: int | None = None
    config: dict
    file_uri: str | None
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class EvalDatasetResponse(BaseModel):
    id: UUID
    library_id: UUID
    name: str
    description: str | None
    source_type: str
    schema_version: str
    sample_count: int
    config: dict
    file_uri: str | None
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

class CreateIntentRequest(BaseModel):
    intent_key: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_.-]+$")
    name_zh: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)
    slot_keys: list[str] = Field(default_factory=list)
    follow_up_enabled: bool = False
    follow_up_prompt: str | None = Field(None, max_length=500)
    hit_responses: list[str] = Field(default_factory=list)
    miss_response: str | None = Field(None, max_length=500)
    sort_order: int = 0


class UpdateIntentRequest(BaseModel):
    name_zh: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)
    slot_keys: list[str] | None = None
    follow_up_enabled: bool | None = None
    follow_up_prompt: str | None = Field(None, max_length=500)
    hit_responses: list[str] | None = None
    miss_response: str | None = Field(None, max_length=500)
    sort_order: int | None = None


class IntentResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    intent_key: str
    name_zh: str
    description: str | None
    slot_keys: list
    follow_up_enabled: bool
    follow_up_prompt: str | None
    hit_responses: list
    miss_response: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Slot
# ---------------------------------------------------------------------------

class CreateSlotRequest(BaseModel):
    slot_key: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    name_zh: str = Field(..., min_length=1, max_length=64)
    description: str | None = Field(None, max_length=500)
    slot_type: str = Field("custom", max_length=16)
    is_required: bool = False
    prompt_text: str | None = Field(None, max_length=500)
    sort_order: int = 0


class UpdateSlotRequest(BaseModel):
    name_zh: str | None = Field(None, min_length=1, max_length=64)
    description: str | None = Field(None, max_length=500)
    slot_type: str | None = Field(None, max_length=16)
    is_required: bool | None = None
    prompt_text: str | None = Field(None, max_length=500)
    sort_order: int | None = None


class SlotResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    slot_key: str
    name_zh: str
    description: str | None
    slot_type: str
    is_required: bool
    prompt_text: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SlotEntity
# ---------------------------------------------------------------------------

class CreateSlotEntityRequest(BaseModel):
    value: str = Field(..., min_length=1, max_length=256)
    synonyms: str | None = Field(None, max_length=1024)
    sort_order: int = 0


class UpdateSlotEntityRequest(BaseModel):
    value: str | None = Field(None, min_length=1, max_length=256)
    synonyms: str | None = Field(None, max_length=1024)
    sort_order: int | None = None


class SlotEntityResponse(BaseModel):
    id: UUID
    slot_id: UUID
    value: str
    synonyms: str | None
    sort_order: int


# ---------------------------------------------------------------------------
# SimilarQuestion
# ---------------------------------------------------------------------------

class CreateSimilarQuestionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=512)
    slot_annotations: dict | list = Field(default_factory=dict)
    source: str = Field("manual", max_length=16)
    sort_order: int = 0


class UpdateSimilarQuestionRequest(BaseModel):
    text: str | None = Field(None, min_length=1, max_length=512)
    slot_annotations: dict | list | None = None
    sort_order: int | None = None


class SimilarQuestionResponse(BaseModel):
    id: UUID
    intent_id: UUID
    text: str
    slot_annotations: dict | list
    source: str
    sort_order: int


# ---------------------------------------------------------------------------
# NegativeExample
# ---------------------------------------------------------------------------

class CreateNegativeExampleRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=512)
    source: str = Field("manual", max_length=16)


class NegativeExampleResponse(BaseModel):
    id: UUID
    intent_id: UUID
    text: str
    source: str


# ---------------------------------------------------------------------------
# TestSession / TestMessage
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    name: str = Field("未命名会话", min_length=1, max_length=128)


class UpdateSessionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class SessionResponse(BaseModel):
    id: UUID
    library_id: UUID
    model_id: UUID
    name: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class TestMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    result: dict
    created_at: datetime
