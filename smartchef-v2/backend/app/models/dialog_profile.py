"""Dialog Profile module ORM models (dd-dialog-profile.md §3)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DialogProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dialog_profiles"
    __table_args__ = (
        Index("idx_dialog_profiles_status", "status"),
        Index("idx_dialog_profiles_created_at", "created_at"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    command_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    route_strategy: Mapped[str] = mapped_column(String(32), default="intent_first", nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_timeout_min: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )

    personas: Mapped[list["Persona"]] = relationship(
        "Persona", back_populates="profile", cascade="all, delete-orphan",
    )
    library_bindings: Mapped[list["ProfileLibraryBinding"]] = relationship(
        "ProfileLibraryBinding", back_populates="profile", cascade="all, delete-orphan",
    )
    published_versions: Mapped[list["PublishedVersion"]] = relationship(
        "PublishedVersion", back_populates="profile", cascade="all, delete-orphan",
    )
    test_sessions: Mapped[list["ProfileTestSession"]] = relationship(
        "ProfileTestSession", back_populates="profile", cascade="all, delete-orphan",
    )


class Persona(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "personas"
    __table_args__ = (
        Index(
            "uq_persona_active_per_profile", "profile_id",
            unique=True, postgresql_where="is_active = true",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    personality: Mapped[str | None] = mapped_column(String(500), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped["DialogProfile"] = relationship("DialogProfile", back_populates="personas")


class ProfileLibraryBinding(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "profile_library_bindings"
    __table_args__ = (
        UniqueConstraint("profile_id", "library_id", name="uq_profile_library"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id", ondelete="CASCADE"), nullable=False,
    )
    library_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intent_libraries.id"), nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)

    profile: Mapped["DialogProfile"] = relationship("DialogProfile", back_populates="library_bindings")
    library: Mapped["IntentLibrary"] = relationship("IntentLibrary", lazy="joined")


class PublishedVersion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "published_versions"
    __table_args__ = (
        Index(
            "uq_published_version_active", "profile_id",
            unique=True, postgresql_where="status = 'active'",
        ),
    )

    version_number: Mapped[str] = mapped_column(String(20), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id", ondelete="CASCADE"), nullable=False,
    )
    config_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    published_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped["DialogProfile"] = relationship("DialogProfile", back_populates="published_versions")


class ProfileTestSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "profile_test_sessions"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), default="未命名会话", nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile: Mapped["DialogProfile"] = relationship("DialogProfile", back_populates="test_sessions")
    messages: Mapped[list["ProfileTestMessage"]] = relationship(
        "ProfileTestMessage", back_populates="session", cascade="all, delete-orphan",
    )


class ProfileTestMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "profile_test_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profile_test_sessions.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    debug_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    session: Mapped["ProfileTestSession"] = relationship("ProfileTestSession", back_populates="messages")
