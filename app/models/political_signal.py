"""Aggregated political signal model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PoliticalSignal(Base):
    __tablename__ = "political_signal"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    hours_to_next_major_event: Mapped[int | None] = mapped_column(Integer)
    next_event_type: Mapped[str | None] = mapped_column(String(50))
    next_event_expected_volatility: Mapped[str | None] = mapped_column(String(10))
    upcoming_events_7d: Mapped[int | None] = mapped_column(Integer)
    upcoming_high_impact_7d: Mapped[int | None] = mapped_column(Integer)

    news_volume_1h: Mapped[int | None] = mapped_column(Integer)
    news_volume_24h: Mapped[int | None] = mapped_column(Integer)
    avg_news_sentiment_1h: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    avg_news_sentiment_24h: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    max_urgency_1h: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    dominant_narrative: Mapped[str | None] = mapped_column(String(100))
    narrative_strength: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    narrative_direction: Mapped[str | None] = mapped_column(String(10))

    political_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
