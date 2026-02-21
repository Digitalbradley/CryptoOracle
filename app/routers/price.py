"""Price data API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price_data import PriceData

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/{symbol}")
def get_prices(
    symbol: str,
    timeframe: str = Query("1h", description="Candle timeframe: 1h, 4h, 1d"),
    limit: int = Query(100, ge=1, le=1000, description="Number of candles"),
    db: Session = Depends(get_db),
):
    """Get the most recent candles for a symbol."""
    # Normalize symbol: accept both BTC/USDT and BTC-USDT
    symbol = symbol.replace("-", "/").upper()

    stmt = (
        select(PriceData)
        .where(PriceData.symbol == symbol, PriceData.timeframe == timeframe)
        .order_by(PriceData.timestamp.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(rows),
        "candles": [
            {
                "timestamp": r.timestamp.isoformat(),
                "open": str(r.open),
                "high": str(r.high),
                "low": str(r.low),
                "close": str(r.close),
                "volume": str(r.volume),
            }
            for r in reversed(rows)  # oldest first
        ],
    }


@router.get("/{symbol}/history")
def get_price_history(
    symbol: str,
    timeframe: str = Query("1d", description="Candle timeframe"),
    start: datetime | None = Query(None, description="Start datetime (ISO 8601)"),
    end: datetime | None = Query(None, description="End datetime (ISO 8601)"),
    db: Session = Depends(get_db),
):
    """Get price history for a symbol within a date range."""
    symbol = symbol.replace("-", "/").upper()

    stmt = select(PriceData).where(
        PriceData.symbol == symbol,
        PriceData.timeframe == timeframe,
    )
    if start:
        stmt = stmt.where(PriceData.timestamp >= start)
    if end:
        stmt = stmt.where(PriceData.timestamp <= end)
    stmt = stmt.order_by(PriceData.timestamp.asc())

    rows = db.execute(stmt).scalars().all()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(rows),
        "candles": [
            {
                "timestamp": r.timestamp.isoformat(),
                "open": str(r.open),
                "high": str(r.high),
                "low": str(r.low),
                "close": str(r.close),
                "volume": str(r.volume),
            }
            for r in rows
        ],
    }
