"""OHLCV price data model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceData(Base):
    __tablename__ = "price_data"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    exchange: Mapped[str] = mapped_column(String(30), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(5), primary_key=True)
    open: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    high: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    low: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    close: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    volume: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))

    __table_args__ = (
        Index("idx_price_symbol_time", "symbol", "timestamp"),
    )
