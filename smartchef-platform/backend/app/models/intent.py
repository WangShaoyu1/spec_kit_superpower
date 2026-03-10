import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class Intent(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "intents"

    intent_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    slots: Mapped[list["Slot"]] = relationship(
        back_populates="intent", cascade="all, delete-orphan", lazy="selectin"
    )
    training_data: Mapped[list["TrainingData"]] = relationship(
        back_populates="intent", cascade="all, delete-orphan", lazy="selectin"
    )


class Slot(UUIDPrimaryKey, Base):
    __tablename__ = "slots"

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False
    )
    slot_key: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    intent: Mapped["Intent"] = relationship(back_populates="slots")

    __table_args__ = (
        __import__("sqlalchemy").UniqueConstraint("intent_id", "slot_key", name="uq_slot_intent_key"),
    )


class TrainingData(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "training_data"

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    slot_annotations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_auto_translated: Mapped[bool] = mapped_column(Boolean, default=False)

    intent: Mapped["Intent"] = relationship(back_populates="training_data")
