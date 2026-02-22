"""Confluence score API endpoints."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.confluence_scores import ConfluenceScores
from app.models.signal_weights import SignalWeights
from app.services.confluence_engine import ConfluenceEngine
from app.utils import normalize_symbol

router = APIRouter(tags=["confluence"])


class WeightUpdate(BaseModel):
    ta: float = 0.20
    onchain: float = 0.15
    celestial: float = 0.12
    numerology: float = 0.08
    sentiment: float = 0.12
    political: float = 0.13
    macro: float = 0.20


# ---- Static routes first (before {symbol} wildcard) ----

@router.get("/api/confluence/weights")
def get_weights(db: Session = Depends(get_db)):
    """Get the current active weight profile."""
    engine = ConfluenceEngine()
    weights = engine.get_active_weights(db)
    return {"profile": "active", "weights": weights}


@router.post("/api/confluence/weights")
def update_weights(body: WeightUpdate, db: Session = Depends(get_db)):
    """Update signal weights. Creates a new profile or updates existing."""
    total = (body.ta + body.onchain + body.celestial + body.numerology
             + body.sentiment + body.political + body.macro)
    if abs(total - 1.0) > 0.01:
        return {"error": f"Weights must sum to 1.0 (got {total:.4f})"}

    # Deactivate all current profiles
    current = db.execute(
        select(SignalWeights).where(SignalWeights.is_active.is_(True))
    ).scalars().all()
    for row in current:
        row.is_active = False

    # Create new profile
    profile = SignalWeights(
        profile_name="custom",
        ta_weight=Decimal(str(body.ta)),
        onchain_weight=Decimal(str(body.onchain)),
        celestial_weight=Decimal(str(body.celestial)),
        numerology_weight=Decimal(str(body.numerology)),
        sentiment_weight=Decimal(str(body.sentiment)),
        political_weight=Decimal(str(body.political)),
        macro_weight=Decimal(str(body.macro)),
        is_active=True,
    )
    db.add(profile)
    db.commit()

    return {
        "status": "updated",
        "weights": {
            "ta": body.ta,
            "onchain": body.onchain,
            "celestial": body.celestial,
            "numerology": body.numerology,
            "sentiment": body.sentiment,
            "political": body.political,
            "macro": body.macro,
        },
    }


# ---- Parameterized routes ----

@router.get("/api/confluence/{symbol}")
def get_confluence(
    symbol: str,
    timeframe: str = Query("1h"),
    db: Session = Depends(get_db),
):
    """Get current confluence score with full layer breakdown.

    Computes on-the-fly from latest layer scores.
    """
    symbol = normalize_symbol(symbol)
    engine = ConfluenceEngine()
    result = engine.compute_and_store(db, symbol, timeframe)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "scores": {
            "ta_score": result.get("ta_score"),
            "onchain_score": result.get("onchain_score"),
            "celestial_score": result.get("celestial_score"),
            "numerology_score": result.get("numerology_score"),
            "sentiment_score": result.get("sentiment_score"),
            "political_score": result.get("political_score"),
            "macro_score": result.get("macro_score"),
        },
        "composite_score": result["composite_score"],
        "signal_strength": result["signal_strength"],
        "aligned_layers": result["aligned_layers"],
        "alignment_count": result["alignment_count"],
        "weights": result["weights"],
    }


@router.get("/api/confluence/{symbol}/history")
def get_confluence_history(
    symbol: str,
    timeframe: str = Query("1d"),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get historical confluence scores."""
    symbol = normalize_symbol(symbol)
    query = select(ConfluenceScores).where(
        ConfluenceScores.symbol == symbol,
        ConfluenceScores.timeframe == timeframe,
    )

    if start:
        query = query.where(ConfluenceScores.timestamp >= start)
    if end:
        query = query.where(ConfluenceScores.timestamp <= end)

    query = query.order_by(ConfluenceScores.timestamp.desc()).limit(limit)
    rows = db.execute(query).scalars().all()

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(rows),
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "composite_score": str(r.composite_score) if r.composite_score else None,
                "signal_strength": r.signal_strength,
                "alignment_count": r.alignment_count,
                "ta_score": str(r.ta_score) if r.ta_score else None,
                "celestial_score": str(r.celestial_score) if r.celestial_score else None,
                "numerology_score": str(r.numerology_score) if r.numerology_score else None,
                "sentiment_score": str(r.sentiment_score) if r.sentiment_score else None,
                "onchain_score": str(r.onchain_score) if r.onchain_score else None,
                "political_score": str(r.political_score) if r.political_score else None,
                "macro_score": str(r.macro_score) if r.macro_score else None,
            }
            for r in rows
        ],
    }
