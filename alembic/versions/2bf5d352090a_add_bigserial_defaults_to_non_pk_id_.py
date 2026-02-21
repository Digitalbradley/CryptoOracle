"""add bigserial defaults to non-pk id columns

Revision ID: 2bf5d352090a
Revises: 16bd2299cf52
Create Date: 2026-02-21 12:49:59.361327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bf5d352090a'
down_revision: Union[str, Sequence[str], None] = '16bd2299cf52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that have a non-PK 'id' column (BigInteger, autoincrement)
# that needs a sequence default added so inserts work without explicit id.
TABLES = ["price_data", "ta_indicators", "celestial_state", "numerology_daily"]


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
