import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class Role(UUIDPrimaryKey, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at = TimestampMixin.created_at

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    role: Mapped[Role | None] = relationship(back_populates="users", lazy="joined")
