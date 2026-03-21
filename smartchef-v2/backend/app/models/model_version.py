"""T012: LibraryModelVersion ORM model (dd-intent-library.md §3.4)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

MODEL_STATUS_CHOICES = ("draft", "training", "trained", "evaluating", "testable", "published", "archived")


class LibraryModelVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "library_model_versions"
    __table_args__ = (
        Index("idx_lmv_library_id", "library_id"),
        Index("idx_lmv_status", "status"),
        Index(
            "uq_lmv_testable", "library_id",
            unique=True, postgresql_where="is_testable = true",
        ),
        Index(
            "uq_lmv_published", "library_id",
            unique=True, postgresql_where="is_published = true",
        ),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_libraries.id"), nullable=False
    )
    version_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    train_dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_datasets.id", ondelete="SET NULL"), nullable=True
    )
    train_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    artifact_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    package_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_testable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    library: Mapped["IntentLibrary"] = relationship("IntentLibrary", back_populates="model_versions")
    train_dataset: Mapped["TrainingDataset | None"] = relationship("TrainingDataset")
    evaluation_runs: Mapped[list["EvaluationRun"]] = relationship(
        "EvaluationRun", back_populates="model_version", cascade="all, delete-orphan"
    )
    test_sessions: Mapped[list["IntentTestSession"]] = relationship(
        "IntentTestSession", back_populates="model_version", cascade="all, delete-orphan"
    )
