"""add xai_policy_events table

Phase B: Policy Pipeline tracking for XAI module.
Stores classified regulatory/policy events from BIS, FSB, SEC, etc.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create xai_policy_events table."""
    op.create_table('xai_policy_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('cross_border_relevance', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('dlt_favorability', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('stablecoin_stance', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('regulatory_direction', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('timeline_urgency', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('xrp_mentioned', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('policy_impact_score', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'title', name='uq_xai_policy_source_title'),
    )
    op.create_index('idx_xai_policy_ts', 'xai_policy_events', ['timestamp'], unique=False)


def downgrade() -> None:
    """Drop xai_policy_events table."""
    op.drop_index('idx_xai_policy_ts', table_name='xai_policy_events')
    op.drop_table('xai_policy_events')
