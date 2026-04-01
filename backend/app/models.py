from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
    role_key: Mapped[str] = mapped_column(String(20), ForeignKey("role_definition.role_key"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    is_builtin_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RoleDefinition(Base):
    __tablename__ = "role_definition"

    role_key: Mapped[str] = mapped_column(String(20), primary_key=True)
    role_label: Mapped[str] = mapped_column(String(50))
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CapabilityDefinition(Base):
    __tablename__ = "capability_definition"

    capability_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(String(100))
    condition_note: Mapped[str | None] = mapped_column(String(100), nullable=True)
    module_key: Mapped[str] = mapped_column(String(40))


class RoleCapabilityBinding(Base):
    __tablename__ = "role_capability_binding"

    role_key: Mapped[str] = mapped_column(String(20), ForeignKey("role_definition.role_key"), primary_key=True)
    capability_key: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("capability_definition.capability_key"),
        primary_key=True,
    )
    condition_note: Mapped[str | None] = mapped_column(String(100), nullable=True)


class AuthSession(Base):
    __tablename__ = "auth_session"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("user_account.id"), index=True)
    token_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[str] = mapped_column(String(32))
    target_user_id: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(40))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommandLibrary(Base):
    __tablename__ = "command_library"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    library_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(8), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    model_limit: Mapped[int] = mapped_column(Integer, default=5)
    default_thresholds_json: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LibraryDataset(Base):
    __tablename__ = "library_dataset"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    library_id: Mapped[str] = mapped_column(String(32), ForeignKey("command_library.id"), index=True)
    dataset_type: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(20))
    # Keep the 1:1 dataset binding in application logic to avoid a drop-cycle in PostgreSQL.
    bound_model_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")
    payload_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LibraryModelVersion(Base):
    __tablename__ = "library_model_version"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    library_id: Mapped[str] = mapped_column(String(32), ForeignKey("command_library.id"), index=True)
    version_name: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), index=True)
    training_dataset_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("library_dataset.id"), nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_testable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_run"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(32), ForeignKey("library_model_version.id"), index=True)
    dataset_id: Mapped[str] = mapped_column(String(32), ForeignKey("library_dataset.id"))
    status: Mapped[str] = mapped_column(String(20), index=True)
    threshold_snapshot_json: Mapped[str] = mapped_column(Text)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    slot_f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_p95_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class KnowledgeCategory(Base):
    __tablename__ = "knowledge_category"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    icon: Mapped[str] = mapped_column(String(8))
    description: Mapped[str] = mapped_column(Text, default="")
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    ready_document_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="empty", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    category_id: Mapped[str] = mapped_column(String(32), ForeignKey("knowledge_category.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    format: Mapped[str] = mapped_column(String(20), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="uploading", index=True)
    source_text: Mapped[str] = mapped_column(Text, default="")
    valid_content_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    filtered_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    index_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeRetrievalProbe(Base):
    __tablename__ = "knowledge_retrieval_probe"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(32), ForeignKey("knowledge_document.id"), index=True)
    query: Mapped[str] = mapped_column(String(300))
    hit: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DialogProfile(Base):
    __tablename__ = "dialog_profile"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    llm_model: Mapped[str] = mapped_column(String(50))
    routing_strategy: Mapped[str] = mapped_column(String(30))
    persona_name: Mapped[str] = mapped_column(String(50))
    persona_prompt: Mapped[str] = mapped_column(Text, default="")
    intent_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    session_timeout_minutes: Mapped[int] = mapped_column(Integer, default=15)
    knowledge_base_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    publish_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DialogProfileLibraryBinding(Base):
    __tablename__ = "dialog_profile_library_binding"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(32), ForeignKey("dialog_profile.id"), index=True)
    library_id: Mapped[str] = mapped_column(String(32), ForeignKey("command_library.id"), index=True)
    library_name: Mapped[str] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(8), default="zh", index=True)
    published_model_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PublishedVersion(Base):
    __tablename__ = "published_version"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(30), index=True)
    entity_id: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TestSession(Base):
    __tablename__ = "test_session"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(32), ForeignKey("dialog_profile.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    device_context_json: Mapped[str] = mapped_column(Text, default="{}")
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TestSessionMessage(Base):
    __tablename__ = "test_session_message"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("test_session.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    text: Mapped[str] = mapped_column(Text)
    debug_trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeviceSession(Base):
    __tablename__ = "device_session"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    profile_id: Mapped[str] = mapped_column(String(32), ForeignKey("dialog_profile.id"), index=True)
    profile_version: Mapped[int] = mapped_column(Integer, default=0)
    device_context_json: Mapped[str] = mapped_column(Text, default="{}")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DevicePrivacyDeleteRequest(Base):
    __tablename__ = "device_privacy_delete_request"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    requested_by: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    confirmation_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class BatchTestRun(Base):
    __tablename__ = "batch_test_run"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    profile_id: Mapped[str] = mapped_column(String(32), ForeignKey("dialog_profile.id"), index=True)
    profile_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    case_count: Mapped[int] = mapped_column(Integer, default=0)
    executed_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_p95_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    threshold_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    analysis_status: Mapped[str] = mapped_column(String(20), default="not_needed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BatchTestCase(Base):
    __tablename__ = "batch_test_case"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(32), ForeignKey("batch_test_run.id"), index=True)
    case_no: Mapped[str] = mapped_column(String(20))
    utterance: Mapped[str] = mapped_column(String(300))
    expected_route: Mapped[str] = mapped_column(String(30))
    expected_intent: Mapped[str | None] = mapped_column(String(80), nullable=True)
    expected_slots_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="auto")
    tuned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BatchTestResult(Base):
    __tablename__ = "batch_test_result"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(32), ForeignKey("batch_test_run.id"), index=True)
    case_id: Mapped[str] = mapped_column(String(32), ForeignKey("batch_test_case.id"), index=True)
    actual_route: Mapped[str] = mapped_column(String(30))
    actual_intent: Mapped[str | None] = mapped_column(String(80), nullable=True)
    actual_slots_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BatchTestAnalysis(Base):
    __tablename__ = "batch_test_analysis"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(32), ForeignKey("batch_test_run.id"), index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    confusion_matrix_json: Mapped[str] = mapped_column(Text, default="[]")
    root_causes_json: Mapped[str] = mapped_column(Text, default="[]")
    recommendations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RequestLog(Base):
    __tablename__ = "request_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    profile_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    route_type: Mapped[str] = mapped_column(String(30), index=True)
    intent_name: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, index=True)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    accuracy_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    request_json: Mapped[str] = mapped_column(Text, default="{}")
    response_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class MonitoringAlertRule(Base):
    __tablename__ = "monitoring_alert_rule"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    metric_key: Mapped[str] = mapped_column(String(40), index=True)
    comparator: Mapped[str] = mapped_column(String(10))
    threshold: Mapped[float] = mapped_column(Float)
    window_minutes: Mapped[int] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MonitoringAlertEvent(Base):
    __tablename__ = "monitoring_alert_event"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(32), ForeignKey("monitoring_alert_rule.id"), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), index=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")


class MonitoringMetricSnapshot(Base):
    __tablename__ = "monitoring_metric_snapshot"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    window_key: Mapped[str] = mapped_column(String(20), index=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    qps: Mapped[float] = mapped_column(Float, default=0)
    avg_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    p95_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    p99_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_rate: Mapped[float] = mapped_column(Float, default=0)
    route_distribution_json: Mapped[str] = mapped_column(Text, default="[]")
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
