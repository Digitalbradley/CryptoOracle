"""Technical analysis indicators model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TAIndicators(Base):
    __tablename__ = "ta_indicators"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(5), primary_key=True)

    # Momentum
    rsi_14: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    rsi_7: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    macd_line: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    macd_signal: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    macd_histogram: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    stoch_k: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    stoch_d: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))

    # Trend
    sma_20: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    sma_50: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    sma_200: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    ema_12: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    ema_26: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))

    # Volatility
    bb_upper: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    bb_middle: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    bb_lower: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    atr_14: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))

    # Fibonacci
    fib_0: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    fib_236: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    fib_382: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    fib_500: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    fib_618: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    fib_786: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    fib_1000: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))

    # Composite
    ta_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
