"""TA signal API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ta_indicators import TAIndicators
from app.utils import normalize_symbol

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _indicator_to_dict(row: TAIndicators) -> dict:
    """Convert a TAIndicators row to a JSON-serializable dict."""
    return {
        "timestamp": row.timestamp.isoformat(),
        "symbol": row.symbol,
        "timeframe": row.timeframe,
        "rsi_14": str(row.rsi_14) if row.rsi_14 is not None else None,
        "rsi_7": str(row.rsi_7) if row.rsi_7 is not None else None,
        "macd_line": str(row.macd_line) if row.macd_line is not None else None,
        "macd_signal": str(row.macd_signal) if row.macd_signal is not None else None,
        "macd_histogram": str(row.macd_histogram) if row.macd_histogram is not None else None,
        "stoch_k": str(row.stoch_k) if row.stoch_k is not None else None,
        "stoch_d": str(row.stoch_d) if row.stoch_d is not None else None,
        "sma_20": str(row.sma_20) if row.sma_20 is not None else None,
        "sma_50": str(row.sma_50) if row.sma_50 is not None else None,
        "sma_200": str(row.sma_200) if row.sma_200 is not None else None,
        "ema_12": str(row.ema_12) if row.ema_12 is not None else None,
        "ema_26": str(row.ema_26) if row.ema_26 is not None else None,
        "bb_upper": str(row.bb_upper) if row.bb_upper is not None else None,
        "bb_middle": str(row.bb_middle) if row.bb_middle is not None else None,
        "bb_lower": str(row.bb_lower) if row.bb_lower is not None else None,
        "atr_14": str(row.atr_14) if row.atr_14 is not None else None,
        "fib_0": str(row.fib_0) if row.fib_0 is not None else None,
        "fib_236": str(row.fib_236) if row.fib_236 is not None else None,
        "fib_382": str(row.fib_382) if row.fib_382 is not None else None,
        "fib_500": str(row.fib_500) if row.fib_500 is not None else None,
        "fib_618": str(row.fib_618) if row.fib_618 is not None else None,
        "fib_786": str(row.fib_786) if row.fib_786 is not None else None,
        "fib_1000": str(row.fib_1000) if row.fib_1000 is not None else None,
        "ta_score": str(row.ta_score) if row.ta_score is not None else None,
    }


@router.get("/ta/{symbol}")
def get_ta_indicators(
    symbol: str,
    timeframe: str = Query("1h", description="Candle timeframe"),
    db: Session = Depends(get_db),
):
    """Get the latest TA indicators for a symbol."""
    symbol = normalize_symbol(symbol)

    stmt = (
        select(TAIndicators)
        .where(TAIndicators.symbol == symbol, TAIndicators.timeframe == timeframe)
        .order_by(TAIndicators.timestamp.desc())
        .limit(1)
    )
    row = db.execute(stmt).scalar_one_or_none()

    if row is None:
        return {"symbol": symbol, "timeframe": timeframe, "indicators": None}

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "indicators": _indicator_to_dict(row),
    }


@router.get("/ta/{symbol}/history")
def get_ta_history(
    symbol: str,
    timeframe: str = Query("1d", description="Candle timeframe"),
    start: datetime | None = Query(None, description="Start datetime (ISO 8601)"),
    end: datetime | None = Query(None, description="End datetime (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records"),
    db: Session = Depends(get_db),
):
    """Get historical TA indicators for a symbol."""
    symbol = normalize_symbol(symbol)

    stmt = select(TAIndicators).where(
        TAIndicators.symbol == symbol,
        TAIndicators.timeframe == timeframe,
    )
    if start:
        stmt = stmt.where(TAIndicators.timestamp >= start)
    if end:
        stmt = stmt.where(TAIndicators.timestamp <= end)
    stmt = stmt.order_by(TAIndicators.timestamp.desc()).limit(limit)

    rows = db.execute(stmt).scalars().all()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(rows),
        "data": [_indicator_to_dict(r) for r in reversed(rows)],
    }
