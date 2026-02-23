"""add bigserial default to political_news non-pk id column

Revision ID: e3c4d5f6a7b8
Revises: d2b3c4e5f6a7
Create Date: 2026-02-23 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3c4d5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'd2b3c4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add BIGSERIAL-like sequence default to political_news.id."""
    op.execute("CREATE SEQUENCE IF NOT EXISTS political_news_id_seq")
    op.execute(
        "ALTER TABLE political_news ALTER COLUMN id SET DEFAULT nextval('political_news_id_seq')"
    )
    op.execute("ALTER SEQUENCE political_news_id_seq OWNED BY political_news.id")


def downgrade() -> None:
    """Remove sequence default from political_news.id."""
    op.execute("ALTER TABLE political_news ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS political_news_id_seq")
