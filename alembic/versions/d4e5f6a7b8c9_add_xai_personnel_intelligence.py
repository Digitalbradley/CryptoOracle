"""add xai_personnel_intelligence table

Phase C: Personnel Intelligence tracking for XAI module.
Stores classified statements from key decision-makers.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-01 16:00:00.000000

"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "xai_personnel_intelligence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("xai_tracked_entities.id"), nullable=True),
        sa.Column("person_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(300), nullable=True),
        sa.Column("statement_type", sa.String(30), nullable=True),
        sa.Column("source_title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("cross_border_urgency", sa.DECIMAL(3, 2), nullable=True),
        sa.Column("dlt_favorability", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("stablecoin_stance", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("timeline_urgency", sa.DECIMAL(3, 2), nullable=True),
        sa.Column("xrp_mentioned", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("key_quote", sa.Text(), nullable=True),
        sa.Column("sentiment_score", sa.DECIMAL(4, 2), nullable=True),
        sa.Column("influence_weight", sa.DECIMAL(3, 1), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_name", "source_title", name="uq_xai_personnel_person_source"),
    )
    op.create_index("idx_xai_personnel_ts", "xai_personnel_intelligence", ["timestamp"])


def downgrade() -> None:
    op.drop_index("idx_xai_personnel_ts", table_name="xai_personnel_intelligence")
    op.drop_table("xai_personnel_intelligence")
