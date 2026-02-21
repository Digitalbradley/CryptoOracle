"""Layer 1: Traditional Technical Analysis signal engine.

Computes RSI, MACD, Stochastic, Bollinger Bands, SMA, EMA, ATR,
Fibonacci retracements from OHLCV data.
Outputs ta_score in range -1.0 to +1.0.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.price_data import PriceData
from app.models.ta_indicators import TAIndicators
from app.services.ta_compute import compute_all, compute_ta_score

logger = logging.getLogger(__name__)

# Minimum candles required for SMA-200
MIN_CANDLES = 200


class TechnicalAnalyzer:
    """Compute TA indicators and composite score from price data."""

    def compute_indicators(
        self,
        symbol: str,
        timeframe: str,
        db: Session,
    ) -> dict | None:
        """Compute all TA indicators for the latest candle.

        Loads the most recent candles from price_data, computes indicators
        via ta_compute, and upserts the result into ta_indicators.

        Returns:
            Dict of indicator values, or None if insufficient data.
        """
        # Load recent candles ordered by timestamp
        stmt = (
            select(PriceData)
            .where(PriceData.symbol == symbol, PriceData.timeframe == timeframe)
            .order_by(PriceData.timestamp.desc())
            .limit(MIN_CANDLES + 50)  # extra buffer
        )
        rows = db.execute(stmt).scalars().all()

        if len(rows) < MIN_CANDLES:
            logger.warning(
                "Insufficient data for %s %s: %d candles (need %d)",
                symbol, timeframe, len(rows), MIN_CANDLES,
            )
            return None

        # Convert to DataFrame (reverse so oldest first)
        rows = list(reversed(rows))
        df = pd.DataFrame(
            [
                {
                    "timestamp": r.timestamp,
                    "open": float(r.open) if r.open else 0,
                    "high": float(r.high) if r.high else 0,
                    "low": float(r.low) if r.low else 0,
                    "close": float(r.close) if r.close else 0,
                    "volume": float(r.volume) if r.volume else 0,
                }
                for r in rows
            ]
        )

        # Compute all indicators
        indicators = compute_all(df)

        # Upsert into ta_indicators
        latest_ts = rows[-1].timestamp
        self._upsert_indicators(db, latest_ts, symbol, timeframe, indicators)

        logger.info(
            "TA computed for %s %s at %s — ta_score=%.4f",
            symbol, timeframe, latest_ts.isoformat(),
            indicators.get("ta_score", 0),
        )
        return indicators

    def compute_score(self, indicators: dict) -> float:
        """Compute composite ta_score from indicator values."""
        return compute_ta_score(indicators)

    def _upsert_indicators(
        self,
        db: Session,
        timestamp: datetime,
        symbol: str,
        timeframe: str,
        indicators: dict,
    ) -> None:
        """Upsert computed indicators into ta_indicators table."""
        row = {
            "timestamp": timestamp,
            "symbol": symbol,
            "timeframe": timeframe,
        }
        # Map indicator values to DB columns
        db_columns = [
            "rsi_14", "rsi_7", "macd_line", "macd_signal", "macd_histogram",
            "stoch_k", "stoch_d", "sma_20", "sma_50", "sma_200",
            "ema_12", "ema_26", "bb_upper", "bb_middle", "bb_lower",
            "atr_14", "fib_0", "fib_236", "fib_382", "fib_500",
            "fib_618", "fib_786", "fib_1000", "ta_score",
        ]
        for col in db_columns:
            val = indicators.get(col)
            row[col] = Decimal(str(val)) if val is not None else None

        stmt = pg_insert(TAIndicators).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp", "symbol", "timeframe"],
            set_={col: stmt.excluded[col] for col in db_columns},
        )
        db.execute(stmt)
        db.commit()
