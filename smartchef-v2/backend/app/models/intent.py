"""T014: Intent / SimilarQuestion / NegativeExample ORM models (dd-intent-library.md §3.2, §3.8~3.9)."""

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Intent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "intents"
    __table_args__ = (
        UniqueConstraint("dataset_id", "intent_key", name="uq_intents_dataset_key"),
        Index("idx_intents_dataset_id", "dataset_id"),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_datasets.id", ondelete="CASCADE"), nullable=False
    )
    intent_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slot_keys: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    follow_up_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_prompt: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hit_responses: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    miss_response: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    dataset: Mapped["TrainingDataset"] = relationship("TrainingDataset", back_populates="intents")
    similar_questions: Mapped[list["SimilarQuestion"]] = relationship(
        "SimilarQuestion", back_populates="intent", cascade="all, delete-orphan"
    )
    negative_examples: Mapped[list["NegativeExample"]] = relationship(
        "NegativeExample", back_populates="intent", cascade="all, delete-orphan"
    )


class SimilarQuestion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "similar_questions"
    __table_args__ = (
        Index("idx_sq_intent_id", "intent_id"),
    )

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    slot_annotations: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="manual", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    intent: Mapped["Intent"] = relationship("Intent", back_populates="similar_questions")


class NegativeExample(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "negative_examples"
    __table_args__ = (
        Index("idx_ne_intent_id", "intent_id"),
    )

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="manual", nullable=False)

    intent: Mapped["Intent"] = relationship("Intent", back_populates="negative_examples")
