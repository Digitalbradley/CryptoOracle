"""deduplicate XAI seed data and add unique constraints

Fixes bootstrap idempotency: removes duplicate partnerships, entities,
and calendar events created by multiple bootstrap runs, then adds
unique constraints to prevent future duplicates.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-01 14:00:00.000000

"""
from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Deduplicate xai_partnerships — keep the row with the lowest id for each partner_name
    op.execute("""
        DELETE FROM xai_partnerships
        WHERE id NOT IN (
            SELECT MIN(id) FROM xai_partnerships GROUP BY partner_name
        )
    """)

    # 2. Deduplicate xai_tracked_entities — keep lowest id per (name, institution)
    op.execute("""
        DELETE FROM xai_tracked_entities
        WHERE id NOT IN (
            SELECT MIN(id) FROM xai_tracked_entities GROUP BY name, institution
        )
    """)

    # 3. Deduplicate xai_event_calendar — keep lowest id per (event_date, event_name)
    op.execute("""
        DELETE FROM xai_event_calendar
        WHERE id NOT IN (
            SELECT MIN(id) FROM xai_event_calendar GROUP BY event_date, event_name
        )
    """)

    # 4. Add unique constraints
    op.create_unique_constraint("uq_xai_partner_name", "xai_partnerships", ["partner_name"])
    op.create_unique_constraint("uq_xai_entity_name_inst", "xai_tracked_entities", ["name", "institution"])
    op.create_unique_constraint("uq_xai_event_date_name", "xai_event_calendar", ["event_date", "event_name"])


def downgrade() -> None:
    op.drop_constraint("uq_xai_event_date_name", "xai_event_calendar", type_="unique")
    op.drop_constraint("uq_xai_entity_name_inst", "xai_tracked_entities", type_="unique")
    op.drop_constraint("uq_xai_partner_name", "xai_partnerships", type_="unique")
