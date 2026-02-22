"""Confluence scores model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConfluenceScores(Base):
    __tablename__ = "confluence_scores"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(5), primary_key=True)

    ta_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    onchain_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    celestial_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    numerology_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    sentiment_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    political_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    macro_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    weights: Mapped[dict] = mapped_column(JSON, nullable=False)

    composite_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    signal_strength: Mapped[str | None] = mapped_column(String(10))

    aligned_layers: Mapped[dict | None] = mapped_column(JSON)
    alignment_count: Mapped[int | None] = mapped_column(Integer)
