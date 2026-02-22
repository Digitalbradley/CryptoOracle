"""Political events API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.political_calendar import PoliticalCalendar
from app.models.political_news import PoliticalNews
from app.models.political_signal import PoliticalSignal

router = APIRouter(tags=["political"])


@router.get("/api/political/status")
def get_political_status():
    """Check which political news sources are configured."""
    return {
        "rss": {
            "configured": True,
            "provides": ["CoinDesk", "CoinTelegraph", "The Block"],
        },
        "newsapi": {
            "configured": bool(settings.newsapi_key),
            "provides": ["general news search"],
        },
        "gnews": {
            "configured": bool(settings.gnews_api_key),
            "provides": ["global news search"],
        },
        "claude_classification": {
            "configured": bool(settings.anthropic_api_key),
            "fallback": "keyword-based classification",
        },
        "any_api_source": bool(settings.newsapi_key or settings.gnews_api_key),
    }


@router.get("/api/political/calendar")
def get_calendar_events(
    days_ahead: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Get upcoming political/economic events."""
    from app.services.political_calendar_service import get_upcoming_events

    events = get_upcoming_events(db, days_ahead)
    return {
        "days_ahead": days_ahead,
        "count": len(events),
        "data": events,
    }


@router.get("/api/political/calendar/{event_id}")
def get_calendar_event(event_id: int, db: Session = Depends(get_db)):
    """Get a single calendar event by ID."""
    row = db.execute(
        select(PoliticalCalendar).where(PoliticalCalendar.id == event_id)
    ).scalar_one_or_none()

    if row is None:
        return {"event": None, "message": "Event not found"}

    return {
        "event": {
            "id": row.id,
            "event_date": row.event_date.isoformat(),
            "event_type": row.event_type,
            "category": row.category,
            "title": row.title,
            "description": row.description,
            "country": row.country,
            "expected_volatility": row.expected_volatility,
            "expected_direction": row.expected_direction,
            "crypto_relevance": row.crypto_relevance,
            "actual_outcome": row.actual_outcome,
            "actual_price_impact_pct": str(row.actual_price_impact_pct) if row.actual_price_impact_pct else None,
            "date_gematria_value": row.date_gematria_value,
            "key_figure_gematria": row.key_figure_gematria,
            "event_title_gematria": row.event_title_gematria,
        },
    }


@router.get("/api/political/news")
def get_political_news(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get recent political news articles."""
    from datetime import timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = db.execute(
        select(PoliticalNews)
        .where(PoliticalNews.timestamp >= cutoff)
        .order_by(PoliticalNews.timestamp.desc())
        .limit(limit)
    ).scalars().all()

    return {
        "hours": hours,
        "count": len(rows),
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "source_name": r.source_name,
                "headline": r.headline,
                "source_url": r.source_url,
                "category": r.category,
                "subcategory": r.subcategory,
                "crypto_relevance_score": str(r.crypto_relevance_score) if r.crypto_relevance_score else None,
                "sentiment_score": str(r.sentiment_score) if r.sentiment_score else None,
                "urgency_score": str(r.urgency_score) if r.urgency_score else None,
                "headline_gematria": r.headline_gematria,
            }
            for r in rows
        ],
    }


@router.get("/api/political/news/history")
def get_news_history(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get political news history."""
    rows = db.execute(
        select(PoliticalNews)
        .order_by(PoliticalNews.timestamp.desc())
        .limit(limit)
    ).scalars().all()

    return {
        "count": len(rows),
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "source_name": r.source_name,
                "headline": r.headline,
                "category": r.category,
                "sentiment_score": str(r.sentiment_score) if r.sentiment_score else None,
                "crypto_relevance_score": str(r.crypto_relevance_score) if r.crypto_relevance_score else None,
            }
            for r in rows
        ],
    }


@router.get("/api/political/signal")
def get_political_signal(db: Session = Depends(get_db)):
    """Get the current (latest) political signal."""
    row = db.execute(
        select(PoliticalSignal)
        .order_by(PoliticalSignal.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if row is None:
        return {"signal": None, "message": "No political signal computed yet"}

    return {
        "signal": {
            "timestamp": row.timestamp.isoformat(),
            "political_score": str(row.political_score) if row.political_score else None,
            "hours_to_next_major_event": row.hours_to_next_major_event,
            "next_event_type": row.next_event_type,
            "upcoming_events_7d": row.upcoming_events_7d,
            "upcoming_high_impact_7d": row.upcoming_high_impact_7d,
            "news_volume_1h": row.news_volume_1h,
            "news_volume_24h": row.news_volume_24h,
            "avg_news_sentiment_1h": str(row.avg_news_sentiment_1h) if row.avg_news_sentiment_1h else None,
            "avg_news_sentiment_24h": str(row.avg_news_sentiment_24h) if row.avg_news_sentiment_24h else None,
            "max_urgency_1h": str(row.max_urgency_1h) if row.max_urgency_1h else None,
            "dominant_narrative": row.dominant_narrative,
            "narrative_strength": str(row.narrative_strength) if row.narrative_strength else None,
            "narrative_direction": row.narrative_direction,
        },
    }


@router.get("/api/political/signal/history")
def get_signal_history(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get political signal history."""
    rows = db.execute(
        select(PoliticalSignal)
        .order_by(PoliticalSignal.timestamp.desc())
        .limit(limit)
    ).scalars().all()

    return {
        "count": len(rows),
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "political_score": str(r.political_score) if r.political_score else None,
                "news_volume_24h": r.news_volume_24h,
                "dominant_narrative": r.dominant_narrative,
                "narrative_direction": r.narrative_direction,
            }
            for r in rows
        ],
    }


@router.get("/api/political/narratives")
def get_narratives(db: Session = Depends(get_db)):
    """Get currently active political/macro narratives."""
    from app.services.political_narrative_service import detect_narratives

    narratives = detect_narratives(db)
    return {
        "count": len(narratives),
        "data": narratives,
    }
