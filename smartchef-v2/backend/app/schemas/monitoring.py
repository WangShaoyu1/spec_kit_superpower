"""Pydantic schemas for the monitoring module."""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Dashboard ──────────────────────────────────────────────────────────────

class DomainDistribution(BaseModel):
    domain: str
    count: int
    percentage: float


class PreviousPeriodMetrics(BaseModel):
    request_count: int = 0
    success_rate: float = 0.0
    avg_latency: float = 0.0
    p99_latency: float = 0.0
    domain_distribution: list[DomainDistribution] = []
    qps: float = 0.0
    intent_accuracy: float = 0.0
    dialog_turns: int = 0


class DashboardMetrics(BaseModel):
    request_count: int = 0
    success_rate: float = 0.0
    avg_latency: float = 0.0
    p99_latency: float = 0.0
    active_alerts: int = 0
    domain_distribution: list[DomainDistribution] = []
    qps: float = 0.0
    intent_accuracy: float = 0.0
    dialog_turns: int = 0
    previous_period: PreviousPeriodMetrics | None = None


class TrendPoint(BaseModel):
    time_bucket: str
    request_count: int = 0
    error_count: int = 0
    avg_latency: float = 0.0


# ── Device Logs ────────────────────────────────────────────────────────────

class LogEntry(BaseModel):
    id: str
    request_id: str
    session_id: str | None = None
    device_id: str | None = None
    input_text: str
    domain: str | None = None
    intent: str | None = None
    slots: dict = {}
    confidence: float | None = None
    latency_ms: int | None = None
    status: str
    error_message: str | None = None
    response_text: str | None = None
    model_version: str | None = None
    created_at: str


class SessionTrace(BaseModel):
    session_id: str
    device_id: str | None = None
    messages: list[LogEntry] = []
    total_messages: int = 0
    start_time: str | None = None
    end_time: str | None = None


class DeviceSession(BaseModel):
    session_id: str
    message_count: int
    first_message_at: str
    last_message_at: str
    domains: list[str] = []


# ── Alert Rules ────────────────────────────────────────────────────────────

VALID_METRICS = {
    "accuracy_rate",
    "p95_latency",
    "p99_latency",
    "avg_latency",
    "error_rate",
    "qps",
    "request_count",
}
METRIC_PATTERN = (
    r"^(accuracy_rate|p95_latency|p99_latency|avg_latency|error_rate|qps|request_count)$"
)
VALID_OPERATORS = {"gt", "lt", "gte", "lte", "eq"}
VALID_CHANNELS = {"email", "webhook", "log"}


class CreateAlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    metric: str = Field(..., pattern=METRIC_PATTERN)
    operator: str = Field(..., pattern=r"^(gt|lt|gte|lte|eq)$")
    threshold: float = Field(...)
    window_minutes: int = Field(5, ge=1, le=1440)
    is_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=list)
    description: str | None = Field(None, max_length=500)


class UpdateAlertRuleRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    metric: str | None = Field(None, pattern=METRIC_PATTERN)
    operator: str | None = Field(None, pattern=r"^(gt|lt|gte|lte|eq)$")
    threshold: float | None = None
    window_minutes: int | None = Field(None, ge=1, le=1440)
    is_enabled: bool | None = None
    notification_channels: list[str] | None = None
    description: str | None = Field(None, max_length=500)


class ToggleAlertRuleRequest(BaseModel):
    is_enabled: bool


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    metric: str
    operator: str
    threshold: float
    window_minutes: int
    is_enabled: bool
    notification_channels: list[str]
    description: str | None = None
    created_by: str | None = None
    created_at: str
    updated_at: str
    last_fired_at: str | None = None


# ── Alert Events ───────────────────────────────────────────────────────────

class AlertEventResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str | None = None
    status: str
    metric_value: float
    threshold_value: float
    fired_at: str
    resolved_at: str | None = None
    message: str | None = None
    created_at: str
