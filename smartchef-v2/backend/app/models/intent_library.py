"""T011: IntentLibrary ORM model (dd-intent-library.md §3.1)."""

import uuid

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IntentLibrary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "intent_libraries"
    __table_args__ = (
        Index("idx_intent_libraries_language", "language"),
        Index("idx_intent_libraries_created_at", "created_at"),
    )

    library_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    default_confidence_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    default_intent_f1_threshold: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    default_slot_f1_threshold: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    model_versions: Mapped[list["LibraryModelVersion"]] = relationship(
        "LibraryModelVersion", back_populates="library", cascade="all, delete-orphan"
    )
    training_datasets: Mapped[list["TrainingDataset"]] = relationship(
        "TrainingDataset", back_populates="library", cascade="all, delete-orphan"
    )
    evaluation_datasets: Mapped[list["EvaluationDataset"]] = relationship(
        "EvaluationDataset", back_populates="library", cascade="all, delete-orphan"
    )
