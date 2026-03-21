"""T015: EvaluationRun ORM model (dd-intent-library.md §3.7)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("idx_er_library_id", "library_id"),
        Index("idx_er_model_version_id", "model_version_id"),
        Index("idx_er_status", "status"),
        Index("idx_er_created_at", "created_at"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_libraries.id"), nullable=False
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("library_model_versions.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_datasets.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    threshold_intent_f1: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    threshold_slot_f1: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    result_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    analysis: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    model_version: Mapped["LibraryModelVersion"] = relationship(
        "LibraryModelVersion", back_populates="evaluation_runs"
    )
