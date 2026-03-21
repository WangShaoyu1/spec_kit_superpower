"""T014: Slot / SlotEntity ORM models (dd-intent-library.md §3.3, §3.10)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Slot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint("dataset_id", "slot_key", name="uq_slots_dataset_key"),
        Index("idx_slots_dataset_id", "dataset_id"),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_datasets.id", ondelete="CASCADE"), nullable=False
    )
    slot_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slot_type: Mapped[str] = mapped_column(String(16), default="custom", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prompt_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    dataset: Mapped["TrainingDataset"] = relationship("TrainingDataset", back_populates="slots")
    entities: Mapped[list["SlotEntity"]] = relationship(
        "SlotEntity", back_populates="slot", cascade="all, delete-orphan"
    )


class SlotEntity(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "slot_entities"
    __table_args__ = (
        Index("idx_se_slot_id", "slot_id"),
    )

    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slots.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(256), nullable=False)
    synonyms: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    slot: Mapped["Slot"] = relationship("Slot", back_populates="entities")
