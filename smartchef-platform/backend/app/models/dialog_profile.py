import uuid
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class DialogProfile(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "dialog_profiles"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    persona_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id"), nullable=True
    )
    routing_strategy: Mapped[str] = mapped_column(String(32), default="command_first", nullable=False)
    session_timeout_minutes: Mapped[int] = mapped_column(Integer, default=10)
    intent_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    knowledge_base_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    persona: Mapped["Persona"] = relationship(lazy="joined")
