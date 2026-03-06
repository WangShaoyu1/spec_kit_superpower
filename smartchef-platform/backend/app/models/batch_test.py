import uuid
from sqlalchemy import ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class BatchTestJob(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "batch_test_jobs"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class BatchTestCase(UUIDPrimaryKey, Base):
    __tablename__ = "batch_test_cases"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batch_test_jobs.id", ondelete="CASCADE"), nullable=False
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expected_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actual_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intent_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool | None] = mapped_column(nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    debug_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
