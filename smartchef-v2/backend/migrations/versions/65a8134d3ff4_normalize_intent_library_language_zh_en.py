"""normalize_intent_library_language_zh_en

Revision ID: 65a8134d3ff4
Revises: 432ff104576e
Create Date: 2026-03-19 20:50:33.683829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65a8134d3ff4'
down_revision: Union[str, Sequence[str], None] = '432ff104576e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """LANGUAGE_CONVENTION: 统一 intent_libraries.language 为 zh/en (DD §4.1)."""
    op.execute(
        "UPDATE intent_libraries SET language = 'zh' "
        "WHERE language LIKE 'zh%' AND language != 'zh'"
    )
    op.execute(
        "UPDATE intent_libraries SET language = 'en' "
        "WHERE language LIKE 'en%' AND language != 'en'"
    )


def downgrade() -> None:
    """无法还原，旧 locale 形式已丢失."""
    pass
