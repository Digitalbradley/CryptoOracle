"""add bigserial defaults to phase3 non-pk id columns

Revision ID: 3a7e4c91b8d1
Revises: 2bf5d352090a
Create Date: 2026-02-22 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a7e4c91b8d1'
down_revision: Union[str, Sequence[str], None] = '2bf5d352090a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Phase 3 tables that have a non-PK 'id' column (BigInteger, autoincrement)
# that needs a sequence default added so inserts work without explicit id.
TABLES = ["sentiment_data", "onchain_metrics", "confluence_scores", "political_signal"]


def upgrade() -> None:
    """Add BIGSERIAL-like sequence defaults to non-PK id columns."""
    for table in TABLES:
        seq_name = f"{table}_id_seq"
        op.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq_name}")
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{seq_name}')"
        )
        op.execute(f"ALTER SEQUENCE {seq_name} OWNED BY {table}.id")


def downgrade() -> None:
    """Remove sequence defaults from non-PK id columns."""
    for table in TABLES:
        seq_name = f"{table}_id_seq"
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT")
        op.execute(f"DROP SEQUENCE IF EXISTS {seq_name}")
