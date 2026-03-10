"""告警规则模型（FR-035）。"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class AlertRule(UUIDPrimaryKey, TimestampMixin, Base):
    """
    告警规则：监控指标、阈值、持续时间、通知配置。

    支持指标：accuracy / p95_latency / p99_latency / error_rate
    运算符：lt / gt / lte / gte
    """
    __tablename__ = "alert_rules"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(8), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notification_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
