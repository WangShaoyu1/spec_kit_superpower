"""T015: IntentTestSession / IntentTestMessage ORM models (dd-intent-library.md §3.11~3.12)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IntentTestSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "intent_test_sessions"
    __table_args__ = (
        Index("idx_its_model_id", "model_id"),
        Index("idx_its_library_id", "library_id"),
    )

    library_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_libraries.id"), nullable=False
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("library_model_versions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), default="未命名会话", nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    model_version: Mapped["LibraryModelVersion"] = relationship(
        "LibraryModelVersion", back_populates="test_sessions"
    )
    messages: Mapped[list["IntentTestMessage"]] = relationship(
        "IntentTestMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="IntentTestMessage.created_at.desc()"
    )


class IntentTestMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "intent_test_messages"
    __table_args__ = (
        Index("idx_itm_session_id", "session_id"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_test_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    session: Mapped["IntentTestSession"] = relationship(
        "IntentTestSession", back_populates="messages"
    )
