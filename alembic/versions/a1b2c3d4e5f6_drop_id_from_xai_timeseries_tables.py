"""drop id from xai timeseries tables

The xai_onchain_metrics and xai_composite tables use timestamp as PK.
The extra 'id' column was created as NOT NULL but has no default/sequence,
causing INSERT failures. Drop it since timestamp is the real PK.

Revision ID: a1b2c3d4e5f6
Revises: f4d5e6a7b8c9
Create Date: 2026-02-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f4d5e6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop unnecessary id columns from timeseries XAI tables."""
    op.drop_column('xai_onchain_metrics', 'id')
    op.drop_column('xai_composite', 'id')


def downgrade() -> None:
    """Re-add id columns."""
    op.add_column('xai_composite',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=True))
    op.add_column('xai_onchain_metrics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=True))
