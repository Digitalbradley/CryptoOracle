"""Historical events model for backtesting."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DECIMAL, Index, Integer, JSON, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HistoricalEvents(Base):
    __tablename__ = "historical_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    magnitude_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    price_at_event: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    duration_hours: Mapped[int | None] = mapped_column(Integer)

    days_since_previous_crash: Mapped[int | None] = mapped_column(Integer)
    days_since_previous_pump: Mapped[int | None] = mapped_column(Integer)
    days_since_previous_halving: Mapped[int | None] = mapped_column(Integer)

    lunar_phase_name: Mapped[str | None] = mapped_column(String(20))
    mercury_retrograde: Mapped[bool | None] = mapped_column(Boolean)
    active_aspects_snapshot: Mapped[dict | None] = mapped_column(JSON)

    date_universal_number: Mapped[int | None] = mapped_column(Integer)
    active_cycle_alignments: Mapped[dict | None] = mapped_column(JSON)

    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("idx_events_type_time", "event_type", "timestamp"),
        Index("idx_events_symbol", "symbol", "timestamp"),
    )
