from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class RequestLog(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "request_logs"

    device_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    intent_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
