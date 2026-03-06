from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class Persona(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "personas"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    tone_style: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
