"""Pydantic schemas for Batch Test module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# BatchTest
# ---------------------------------------------------------------------------

class BatchTestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)
    profile_id: UUID | None = None
    accuracy_threshold: float = Field(default=0.95, ge=0, le=1)
    latency_threshold_ms: int = Field(default=2000, ge=0)


class BatchTestOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    profile_id: UUID | None = None
    profile_name: str | None = None
    status: str
    total_cases: int
    completed_cases: int
    accuracy: float | None = None
    precision_score: float | None = None
    recall_score: float | None = None
    accuracy_threshold: float | None = None
    latency_threshold_ms: int | None = None
    p99_latency_ms: int | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchTestStats(BaseModel):
    total: int = 0
    running: int = 0
    completed: int = 0
    avg_accuracy: float | None = None


# ---------------------------------------------------------------------------
# TestCase
# ---------------------------------------------------------------------------

class TestCaseCreate(BaseModel):
    input_text: str = Field(..., min_length=1)
    expected_intent: str | None = Field(None, max_length=128)
    expected_slots: dict = Field(default_factory=dict)
    expected_domain: str | None = Field(None, pattern=r"^(command|knowledge|chitchat)$")
    sort_order: int = 0


class TestCaseUpdate(BaseModel):
    input_text: str | None = Field(None, min_length=1)
    expected_intent: str | None = Field(None, max_length=128)
    expected_slots: dict | None = None
    expected_domain: str | None = Field(None, pattern=r"^(command|knowledge|chitchat)$")
    sort_order: int | None = None


class TestCaseOut(BaseModel):
    id: UUID
    batch_id: UUID
    input_text: str
    expected_intent: str | None = None
    expected_slots: dict = Field(default_factory=dict)
    expected_domain: str | None = None
    sort_order: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TestCaseImportItem(BaseModel):
    input_text: str = Field(..., min_length=1)
    expected_intent: str | None = None
    expected_slots: dict = Field(default_factory=dict)
    expected_domain: str | None = Field(None, pattern=r"^(command|knowledge|chitchat)$")


class TestCaseImportRequest(BaseModel):
    cases: list[TestCaseImportItem] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# TestRun
# ---------------------------------------------------------------------------

class TestRunOut(BaseModel):
    id: UUID
    batch_id: UUID
    case_id: UUID
    input_text: str | None = None
    expected_intent: str | None = None
    actual_domain: str | None = None
    actual_intent: str | None = None
    actual_slots: dict = Field(default_factory=dict)
    confidence: float | None = None
    is_domain_hit: bool | None = None
    is_intent_hit: bool | None = None
    latency_ms: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# TestRunAnalysis
# ---------------------------------------------------------------------------

class GenerateCasesRequest(BaseModel):
    intent_names: list[str] = Field(..., min_length=1)
    samples_per_intent: int = Field(default=5, ge=1, le=100)
    include_knowledge: bool = False
    include_chitchat: bool = False


class TestRunAnalysisOut(BaseModel):
    id: UUID
    batch_id: UUID
    summary: dict = Field(default_factory=dict)
    confusion_top_n: list = Field(default_factory=list)
    slot_error_distribution: list = Field(default_factory=list)
    low_score_samples: list = Field(default_factory=list)
    recommendations: list = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}
