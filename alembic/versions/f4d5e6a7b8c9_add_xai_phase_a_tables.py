"""add XAI phase A tables

Revision ID: f4d5e6a7b8c9
Revises: e3c4d5f6a7b8
Create Date: 2026-02-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4d5e6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'e3c4d5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create XAI tables and add xai_score to confluence/weights."""
    # --- xai_onchain_metrics ---
    op.create_table('xai_onchain_metrics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('xrpl_tx_count', sa.BigInteger(), nullable=True),
        sa.Column('xrpl_payment_volume_usd', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('xrpl_dex_volume_usd', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('rlusd_total_supply', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('rlusd_unique_holders', sa.Integer(), nullable=True),
        sa.Column('rlusd_trust_line_count', sa.Integer(), nullable=True),
        sa.Column('utility_volume_usd', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('speculation_volume_usd', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('utility_to_speculation_ratio', sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column('xrpl_active_addresses', sa.Integer(), nullable=True),
        sa.Column('xrpl_new_accounts', sa.Integer(), nullable=True),
        sa.Column('xrp_exchange_reserve', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('timestamp')
    )
    op.create_index('idx_xai_onchain_ts', 'xai_onchain_metrics', ['timestamp'], unique=False)

    # --- xai_composite ---
    op.create_table('xai_composite',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('policy_pipeline_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('partnership_deployment_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('onchain_utility_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('personnel_intelligence_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('xai_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('utility_to_speculation_ratio', sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column('rlusd_market_cap', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('active_partnership_count', sa.Integer(), nullable=True),
        sa.Column('partnerships_in_production', sa.Integer(), nullable=True),
        sa.Column('adoption_phase', sa.String(length=30), nullable=True),
        sa.Column('weights', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp')
    )
    op.create_index('idx_xai_composite_ts', 'xai_composite', ['timestamp'], unique=False)

    # --- xai_partnerships ---
    op.create_table('xai_partnerships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('partner_name', sa.String(length=200), nullable=False),
        sa.Column('partner_type', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('is_cpmi_member_country', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('partnership_type', sa.String(length=50), nullable=True),
        sa.Column('pipeline_stage', sa.String(length=30), nullable=False),
        sa.Column('stage_score', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('partner_weight', sa.DECIMAL(precision=3, scale=1), nullable=True),
        sa.Column('announced_date', sa.Date(), nullable=True),
        sa.Column('stage_updated_date', sa.Date(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # --- xai_tracked_entities ---
    op.create_table('xai_tracked_entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=300), nullable=True),
        sa.Column('institution', sa.String(length=200), nullable=True),
        sa.Column('tier', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('cpmi_member', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('fsb_member', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('watch_urls', sa.JSON(), nullable=True),
        sa.Column('social_handles', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # --- xai_event_calendar ---
    op.create_table('xai_event_calendar',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_name', sa.String(length=300), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('xrp_relevance', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('potential_impact', sa.String(length=20), nullable=True),
        sa.Column('recurring', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('recurrence_pattern', sa.String(length=50), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # --- Add xai_score to confluence_scores ---
    op.add_column('confluence_scores',
        sa.Column('xai_score', sa.DECIMAL(precision=5, scale=4), nullable=True))

    # --- Add xai_weight to signal_weights ---
    op.add_column('signal_weights',
        sa.Column('xai_weight', sa.DECIMAL(precision=5, scale=4), nullable=False, server_default='0.0000'))


def downgrade() -> None:
    """Remove XAI tables and columns."""
    op.drop_column('signal_weights', 'xai_weight')
    op.drop_column('confluence_scores', 'xai_score')
    op.drop_table('xai_event_calendar')
    op.drop_table('xai_tracked_entities')
    op.drop_table('xai_partnerships')
    op.drop_index('idx_xai_composite_ts', table_name='xai_composite')
    op.drop_table('xai_composite')
    op.drop_index('idx_xai_onchain_ts', table_name='xai_onchain_metrics')
    op.drop_table('xai_onchain_metrics')
