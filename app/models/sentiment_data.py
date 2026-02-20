"""Sentiment data model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SentimentData(Base):
    __tablename__ = "sentiment_data"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)

    fear_greed_index: Mapped[int | None] = mapped_column(Integer)
    fear_greed_label: Mapped[str | None] = mapped_column(String(20))

    social_volume: Mapped[int | None] = mapped_column(Integer)
    social_sentiment: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    social_source: Mapped[str | None] = mapped_column(String(20))

    google_trends_score: Mapped[int | None] = mapped_column(Integer)

    sentiment_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
