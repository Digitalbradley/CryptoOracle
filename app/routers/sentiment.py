"""Sentiment data API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sentiment_data import SentimentData
from app.utils import normalize_symbol

router = APIRouter(tags=["sentiment"])


@router.get("/api/sentiment/{symbol}")
def get_latest_sentiment(symbol: str, db: Session = Depends(get_db)):
    """Get the latest sentiment data for a symbol."""
    symbol = normalize_symbol(symbol)
    row = db.execute(
        select(SentimentData)
        .where(SentimentData.symbol == symbol)
        .order_by(SentimentData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if row is None:
        return {"symbol": symbol, "sentiment": None, "message": "No sentiment data available"}

    return {
        "symbol": symbol,
        "sentiment": {
            "timestamp": row.timestamp.isoformat(),
            "fear_greed_index": row.fear_greed_index,
            "fear_greed_label": row.fear_greed_label,
            "sentiment_score": str(row.sentiment_score) if row.sentiment_score else None,
        },
    }


@router.get("/api/sentiment/{symbol}/history")
def get_sentiment_history(
    symbol: str,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get historical sentiment data for a symbol."""
    symbol = normalize_symbol(symbol)
    query = select(SentimentData).where(SentimentData.symbol == symbol)

    if start:
        query = query.where(SentimentData.timestamp >= start)
    if end:
        query = query.where(SentimentData.timestamp <= end)

    query = query.order_by(SentimentData.timestamp.desc()).limit(limit)
    rows = db.execute(query).scalars().all()

    return {
        "symbol": symbol,
        "count": len(rows),
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "fear_greed_index": r.fear_greed_index,
                "fear_greed_label": r.fear_greed_label,
                "sentiment_score": str(r.sentiment_score) if r.sentiment_score else None,
            }
            for r in rows
        ],
    }
