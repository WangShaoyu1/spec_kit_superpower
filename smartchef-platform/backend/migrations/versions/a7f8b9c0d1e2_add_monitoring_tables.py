"""add_monitoring_tables

为 request_logs、alert_rules 添加高频查询索引。
表结构已在 c12d89f10596（request_logs）、29cc42c3435d（alert_rules）中创建。

Revision ID: a7f8b9c0d1e2
Revises: add_test_suites
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a7f8b9c0d1e2"
down_revision: Union[str, None] = "add_test_suites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # request_logs 表：添加 created_at、domain、intent 索引（device_id 已有）
    op.create_index(
        "ix_request_logs_created_at",
        "request_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_request_logs_domain",
        "request_logs",
        ["domain"],
        unique=False,
    )
    op.create_index(
        "ix_request_logs_intent",
        "request_logs",
        ["intent"],
        unique=False,
    )
    # 复合索引：设备 + 时间（按设备查历史）
    op.create_index(
        "ix_request_logs_device_created",
        "request_logs",
        ["device_id", "created_at"],
        unique=False,
    )

    # alert_rules 表：添加 metric_name、is_enabled 索引
    op.create_index(
        "ix_alert_rules_metric_name",
        "alert_rules",
        ["metric_name"],
        unique=False,
    )
    op.create_index(
        "ix_alert_rules_is_enabled",
        "alert_rules",
        ["is_enabled"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_alert_rules_is_enabled", table_name="alert_rules")
    op.drop_index("ix_alert_rules_metric_name", table_name="alert_rules")
    op.drop_index("ix_request_logs_device_created", table_name="request_logs")
    op.drop_index("ix_request_logs_intent", table_name="request_logs")
    op.drop_index("ix_request_logs_domain", table_name="request_logs")
    op.drop_index("ix_request_logs_created_at", table_name="request_logs")
