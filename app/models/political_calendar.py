"""Political calendar (scheduled events) model."""

import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    Boolean, DECIMAL, Date, Index, Integer, JSON, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PoliticalCalendar(Base):
    __tablename__ = "political_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    event_time: Mapped[dt.datetime | None]
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(5), default="US")

    expected_volatility: Mapped[str | None] = mapped_column(String(10))
    expected_direction: Mapped[str | None] = mapped_column(String(10))
    crypto_relevance: Mapped[int] = mapped_column(Integer, default=5)

    actual_outcome: Mapped[str | None] = mapped_column(Text)
    actual_price_impact_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))

    date_gematria_value: Mapped[int | None] = mapped_column(Integer)
    key_figure_gematria: Mapped[dict | None] = mapped_column(JSON)
    event_title_gematria: Mapped[dict | None] = mapped_column(JSON)

    source_url: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(String(100))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_polcal_date", "event_date"),
        Index("idx_polcal_type", "event_type", "event_date"),
        Index("idx_polcal_category", "category", "event_date"),
    )
