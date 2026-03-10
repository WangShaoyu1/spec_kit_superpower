"""监控相关 Schema（US9 / FR-035）。"""
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ----- 请求日志 -----


class RequestLogResponse(BaseModel):
    """请求日志响应。"""

    id: UUID
    device_id: str
    session_id: str | None = None
    input_text: str
    domain: str
    intent: str | None = None
    response_text: str | None = None
    latency_ms: int
    intent_confidence: float | None = None
    language: str = "zh"
    created_at: datetime

    model_config = {"from_attributes": True}


class LogQueryParams(BaseModel):
    """日志查询参数：设备ID、时间范围、路由类型、意图等。"""

    device_id: str | None = None
    domain: str | None = Field(None, description="路由类型/领域")
    intent: str | None = Field(None, description="意图")
    start_time: datetime | None = None
    end_time: datetime | None = None
    hours: int = Field(24, ge=1, le=720, description="最近 N 小时，与 start/end 二选一")
    limit: int = Field(100, ge=1, le=500)


# ----- 监控指标 -----


class MetricsResponse(BaseModel):
    """监控指标：QPS、延迟、准确率、路由分布。"""

    total_requests: int = Field(..., description="总请求数")
    qps: float = Field(..., description="每秒查询数")
    avg_latency_ms: float = Field(..., description="平均延迟（毫秒）")
    p95_latency_ms: float | None = Field(None, description="P95 延迟（毫秒）")
    p99_latency_ms: float | None = Field(None, description="P99 延迟（毫秒）")
    accuracy: float | None = Field(None, description="准确率（0-1）")
    domain_distribution: dict[str, int] = Field(
        default_factory=dict, description="路由/领域分布"
    )
    unique_devices: int = Field(0, description="独立设备数")
    time_range_hours: int = Field(..., description="统计时间范围（小时）")


# ----- 告警规则 -----


class AlertRuleCreate(BaseModel):
    """告警规则创建。"""

    name: str = Field(..., min_length=1, max_length=128)
    metric_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="指标：accuracy / p95_latency / p99_latency / error_rate",
    )
    operator: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="运算符：lt / gt / lte / gte",
    )
    threshold: Decimal = Field(..., description="阈值")
    duration_minutes: int = Field(..., ge=1, description="持续时间（分钟）")
    notification_config: dict = Field(..., description="通知配置")
    is_enabled: bool = True


class AlertRuleResponse(BaseModel):
    """告警规则响应。"""

    id: UUID
    name: str
    metric_name: str
    operator: str
    threshold: Decimal
    duration_minutes: int
    notification_config: dict
    is_enabled: bool
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleUpdate(BaseModel):
    """告警规则更新。"""

    name: str | None = None
    metric_name: str | None = None
    operator: str | None = None
    threshold: Decimal | None = None
    duration_minutes: int | None = None
    notification_config: dict | None = None
    is_enabled: bool | None = None
