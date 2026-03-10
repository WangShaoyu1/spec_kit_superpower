"""测试套件、用例、报告 ORM 模型。"""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base
from app.models.base import UUIDPrimaryKey, TimestampMixin


class TestSuite(UUIDPrimaryKey, TimestampMixin, Base):
    """测试套件：关联对话方案，可包含多组用例。"""

    __tablename__ = "test_suites"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dialog_profiles.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="suite", cascade="all, delete-orphan"
    )
    reports: Mapped[list["TestReport"]] = relationship(
        "TestReport", back_populates="suite", cascade="all, delete-orphan"
    )


class TestCase(UUIDPrimaryKey, Base):
    """测试用例：属于某测试套件，包含输入与预期。"""

    __tablename__ = "test_suite_cases"

    suite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expected_domain: Mapped[str | None] = mapped_column(String(32), nullable=True)

    suite: Mapped["TestSuite"] = relationship("TestSuite", back_populates="cases")


class TestReport(UUIDPrimaryKey, Base):
    """测试报告：某次批量执行的结果及分析。"""

    __tablename__ = "test_reports"

    suite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False
    )
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    p95_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_passed: Mapped[bool] = mapped_column(nullable=False)
    analysis_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    suite: Mapped["TestSuite"] = relationship("TestSuite", back_populates="reports")
