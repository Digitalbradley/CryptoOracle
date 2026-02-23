"""add bigserial defaults to macro layer 7 non-pk id columns

Revision ID: c1a2b3d4e5f6
Revises: badff7346444
Create Date: 2026-02-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'badff7346444'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Macro Layer 7 tables that have a non-PK 'id' column (BigInteger, autoincrement)
# that needs a sequence default added so inserts work without explicit id.
TABLES = [
    "liquidity_data",
    "rate_data",
    "macro_prices",
    "carry_trade_data",
    "oil_data",
    "macro_liquidity_signal",
]


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
