"""batch test thresholds and p99 latency

Revision ID: a1b2c3d4e5f6
Revises: 65a8134d3ff4
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "65a8134d3ff4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("batch_tests", sa.Column("accuracy_threshold", sa.Float(), nullable=True))
    op.add_column("batch_tests", sa.Column("latency_threshold_ms", sa.Integer(), nullable=True))
    op.add_column("batch_tests", sa.Column("p99_latency_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("batch_tests", "p99_latency_ms")
    op.drop_column("batch_tests", "latency_threshold_ms")
    op.drop_column("batch_tests", "accuracy_threshold")
