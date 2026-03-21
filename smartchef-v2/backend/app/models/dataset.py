"""T013: TrainingDataset + EvaluationDataset ORM models (dd-intent-library.md §3.5~3.6)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TrainingDataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "training_datasets"
    __table_args__ = (
        Index("idx_td_library_id", "library_id"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_libraries.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="manual", nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), default="v1", nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    intent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    file_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    library: Mapped["IntentLibrary"] = relationship("IntentLibrary", back_populates="training_datasets")
    intents: Mapped[list["Intent"]] = relationship(
        "Intent", back_populates="dataset", cascade="all, delete-orphan"
    )
    slots: Mapped[list["Slot"]] = relationship(
        "Slot", back_populates="dataset", cascade="all, delete-orphan"
    )


class EvaluationDataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_datasets"
    __table_args__ = (
        Index("idx_ed_library_id", "library_id"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_libraries.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16), default="manual", nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), default="v1", nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    samples: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    file_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    library: Mapped["IntentLibrary"] = relationship("IntentLibrary", back_populates="evaluation_datasets")
