from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class BatchTestCaseInput(BaseModel):
    input_text: str
    expected_intent: str | None = None
    expected_domain: str | None = None


class BatchTestCreate(BaseModel):
    name: str = Field(..., min_length=1)
    profile_id: UUID
    test_cases: list[BatchTestCaseInput]
    accuracy_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    latency_threshold_ms: int = Field(default=200, ge=0)


class BatchTestCaseResult(BaseModel):
    input_text: str
    expected_intent: str | None
    expected_domain: str | None
    actual_intent: str | None
    actual_domain: str | None
    intent_confidence: float | None
    latency_ms: int | None
    passed: bool | None
    response_text: str | None

    model_config = {"from_attributes": True}


class BatchTestJobInfo(BaseModel):
    id: UUID
    name: str
    profile_id: UUID
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    accuracy: float | None
    avg_latency_ms: float | None
    report: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
