"""add unique constraint to political_calendar (event_date, event_type)

Revision ID: d2b3c4e5f6a7
Revises: c1a2b3d4e5f6
Create Date: 2026-02-23 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2b3c4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Deduplicate any existing rows before adding constraint
    op.execute("""
        DELETE FROM political_calendar a
        USING political_calendar b
        WHERE a.id > b.id
          AND a.event_date = b.event_date
          AND a.event_type = b.event_type
    """)
    op.create_unique_constraint(
        "uq_polcal_date_type", "political_calendar", ["event_date", "event_type"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_polcal_date_type", "political_calendar", type_="unique")
