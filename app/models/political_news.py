"""Political news (real-time) model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PoliticalNews(Base):
    __tablename__ = "political_news"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(
        String(100), primary_key=True, nullable=False
    )
    headline: Mapped[str] = mapped_column(
        String(500), primary_key=True, nullable=False
    )

    source_url: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)

    category: Mapped[str | None] = mapped_column(String(30))
    subcategory: Mapped[str | None] = mapped_column(String(50))
    crypto_relevance_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    sentiment_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    urgency_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    entities: Mapped[dict | None] = mapped_column(JSON)
    headline_gematria: Mapped[dict | None] = mapped_column(JSON)

    mention_velocity: Mapped[int | None] = mapped_column(Integer)
    mention_velocity_1h: Mapped[int | None] = mapped_column(Integer)
    mention_velocity_4h: Mapped[int | None] = mapped_column(Integer)
    peak_velocity: Mapped[int | None] = mapped_column(Integer)
    peak_velocity_time: Mapped[datetime | None]

    btc_price_at_publish: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    btc_price_1h_after: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    btc_price_4h_after: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    btc_price_24h_after: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    actual_impact_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))

    political_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    __table_args__ = (
        Index("idx_polnews_relevance", "crypto_relevance_score", "timestamp"),
        Index("idx_polnews_category", "category", "timestamp"),
    )
