"""add model_id to batch tests

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("batch_tests", sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_batch_tests_model_id",
        "batch_tests",
        "library_model_versions",
        ["model_id"],
        ["id"],
    )
    op.create_index("idx_batch_tests_model_id", "batch_tests", ["model_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_batch_tests_model_id", table_name="batch_tests")
    op.drop_constraint("fk_batch_tests_model_id", "batch_tests", type_="foreignkey")
    op.drop_column("batch_tests", "model_id")
