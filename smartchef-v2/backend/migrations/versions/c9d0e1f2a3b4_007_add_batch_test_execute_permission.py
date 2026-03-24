"""add batch_test_execute permission

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-03-23

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO permissions (id, key, label, module)
            VALUES (:id, 'batch_test_execute', '执行批量测试', '批量测试')
            ON CONFLICT (key) DO UPDATE
            SET label = EXCLUDED.label, module = EXCLUDED.module
            """
        ).bindparams(id=uuid.uuid4())
    )

    op.execute(
        sa.text(
            """
            UPDATE permissions
            SET label = '管理批量测试'
            WHERE key = 'batch_test_write'
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT rp.role_id, p_exec.id
            FROM role_permissions rp
            JOIN permissions p_write ON p_write.id = rp.permission_id
            CROSS JOIN permissions p_exec
            WHERE p_write.key = 'batch_test_write'
              AND p_exec.key = 'batch_test_execute'
              AND NOT EXISTS (
                SELECT 1
                FROM role_permissions existing
                WHERE existing.role_id = rp.role_id
                  AND existing.permission_id = p_exec.id
              )
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id = (SELECT id FROM permissions WHERE key = 'batch_test_execute')
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE key = 'batch_test_execute'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE permissions
            SET label = '执行批量测试'
            WHERE key = 'batch_test_write'
            """
        )
    )
