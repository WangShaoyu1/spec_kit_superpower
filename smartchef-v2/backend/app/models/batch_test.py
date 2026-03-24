"""Batch Test module ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BatchTest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "batch_tests"
    __table_args__ = (
        Index("idx_batch_tests_status", "status"),
        Index("idx_batch_tests_created_at", "created_at"),
        Index("idx_batch_tests_model_id", "model_id"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id"), nullable=True,
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("library_model_versions.id"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    precision_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_threshold_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p99_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

    cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="batch", cascade="all, delete-orphan",
    )
    runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="batch", cascade="all, delete-orphan",
    )
    analyses: Mapped[list["TestRunAnalysis"]] = relationship(
        "TestRunAnalysis", back_populates="batch", cascade="all, delete-orphan",
    )
    profile: Mapped["DialogProfile"] = relationship("DialogProfile", lazy="joined")
    model_version: Mapped["LibraryModelVersion | None"] = relationship("LibraryModelVersion", lazy="joined")


class TestCase(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "test_cases"
    __table_args__ = (
        Index("idx_test_cases_batch_id", "batch_id"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batch_tests.id", ondelete="CASCADE"), nullable=False,
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expected_slots: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    expected_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    batch: Mapped["BatchTest"] = relationship("BatchTest", back_populates="cases")
    runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="case", cascade="all, delete-orphan",
    )


class TestRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "test_runs"
    __table_args__ = (
        Index("idx_test_runs_batch_id", "batch_id"),
        Index("idx_test_runs_case_id", "case_id"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batch_tests.id", ondelete="CASCADE"), nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False,
    )
    actual_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actual_slots: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_domain_hit: Mapped[bool | None] = mapped_column(nullable=True)
    is_intent_hit: Mapped[bool | None] = mapped_column(nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    batch: Mapped["BatchTest"] = relationship("BatchTest", back_populates="runs")
    case: Mapped["TestCase"] = relationship("TestCase", back_populates="runs")


class TestRunAnalysis(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "test_run_analyses"
    __table_args__ = (
        Index("idx_test_run_analyses_batch_id", "batch_id"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batch_tests.id", ondelete="CASCADE"), nullable=False,
    )
    summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confusion_top_n: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    slot_error_distribution: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    low_score_samples: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    recommendations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    batch: Mapped["BatchTest"] = relationship("BatchTest", back_populates="analyses")
