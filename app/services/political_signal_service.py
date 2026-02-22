"""Political signal service — hourly aggregator.

Combines calendar proximity, news sentiment, and narrative detection
into a composite political_score stored in the political_signal table.

Formula: 0.30 * calendar + 0.35 * news + 0.35 * narrative
With black swan override for urgent breaking news.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.political_news import PoliticalNews
from app.models.political_signal import PoliticalSignal
from app.services import political_calendar_service
from app.services import political_news_service
from app.services import political_narrative_service

logger = logging.getLogger(__name__)


def _check_black_swan(db: Session) -> float | None:
    """Check for black swan events (urgency_score > 0.9 in last hour).

    Returns the article's sentiment_score if found, None otherwise.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    row = db.execute(
        select(PoliticalNews)
        .where(
            PoliticalNews.timestamp >= cutoff,
            PoliticalNews.urgency_score > Decimal("0.9"),
        )
        .order_by(PoliticalNews.urgency_score.desc())
        .limit(1)
    ).scalar_one_or_none()

    if row and row.sentiment_score is not None:
        return float(row.sentiment_score)
    return None


def compute_political_signal(db: Session) -> dict:
    """Compute composite political signal from all sub-modules.

    Returns dict matching PoliticalSignal model fields.
    """
    # Gather sub-scores
    calendar_result = political_calendar_service.compute_calendar_score(db)
    calendar_score = calendar_result["score"]

    news_score = political_news_service.compute_news_score(db)

    narrative_score = political_narrative_service.compute_narrative_score(db)
    dominant = political_narrative_service.get_dominant_narrative(db)

    # Black swan override
    black_swan = _check_black_swan(db)
    if black_swan is not None:
        logger.warning("Black swan event detected — overriding political score to %.4f", black_swan)
        composite = black_swan
    else:
        # Standard formula: 0.30 * calendar + 0.35 * news + 0.35 * narrative
        composite = 0.30 * calendar_score + 0.35 * news_score + 0.35 * narrative_score

    composite = round(max(-1.0, min(1.0, composite)), 4)

    # News volume stats
    now = datetime.now(timezone.utc)
    cutoff_1h = now - timedelta(hours=1)
    cutoff_24h = now - timedelta(hours=24)

    news_1h = db.execute(
        select(PoliticalNews)
        .where(PoliticalNews.timestamp >= cutoff_1h)
    ).scalars().all()

    news_24h = db.execute(
        select(PoliticalNews)
        .where(PoliticalNews.timestamp >= cutoff_24h)
    ).scalars().all()

    # Average sentiments
    sentiments_1h = [float(r.sentiment_score) for r in news_1h if r.sentiment_score is not None]
    sentiments_24h = [float(r.sentiment_score) for r in news_24h if r.sentiment_score is not None]
    urgencies_1h = [float(r.urgency_score) for r in news_1h if r.urgency_score is not None]

    return {
        "timestamp": now.replace(minute=0, second=0, microsecond=0),
        "hours_to_next_major_event": calendar_result.get("hours_to_next"),
        "next_event_type": calendar_result.get("next_event_type"),
        "next_event_expected_volatility": None,  # Could be enriched
        "upcoming_events_7d": calendar_result.get("upcoming_7d"),
        "upcoming_high_impact_7d": calendar_result.get("upcoming_high_impact_7d"),
        "news_volume_1h": len(news_1h),
        "news_volume_24h": len(news_24h),
        "avg_news_sentiment_1h": Decimal(str(round(
            sum(sentiments_1h) / len(sentiments_1h), 4
        ))) if sentiments_1h else None,
        "avg_news_sentiment_24h": Decimal(str(round(
            sum(sentiments_24h) / len(sentiments_24h), 4
        ))) if sentiments_24h else None,
        "max_urgency_1h": Decimal(str(round(max(urgencies_1h), 4))) if urgencies_1h else None,
        "dominant_narrative": dominant["narrative"] if dominant else None,
        "narrative_strength": Decimal(str(dominant["strength"])) if dominant else None,
        "narrative_direction": dominant["direction"] if dominant else None,
        "political_score": Decimal(str(composite)),
    }


def upsert_signal(db: Session, data: dict, *, commit: bool = True) -> None:
    """Upsert political signal into the database."""
    stmt = pg_insert(PoliticalSignal).values([data])
    stmt = stmt.on_conflict_do_update(
        index_elements=["timestamp"],
        set_={
            "hours_to_next_major_event": stmt.excluded.hours_to_next_major_event,
            "next_event_type": stmt.excluded.next_event_type,
            "next_event_expected_volatility": stmt.excluded.next_event_expected_volatility,
            "upcoming_events_7d": stmt.excluded.upcoming_events_7d,
            "upcoming_high_impact_7d": stmt.excluded.upcoming_high_impact_7d,
            "news_volume_1h": stmt.excluded.news_volume_1h,
            "news_volume_24h": stmt.excluded.news_volume_24h,
            "avg_news_sentiment_1h": stmt.excluded.avg_news_sentiment_1h,
            "avg_news_sentiment_24h": stmt.excluded.avg_news_sentiment_24h,
            "max_urgency_1h": stmt.excluded.max_urgency_1h,
            "dominant_narrative": stmt.excluded.dominant_narrative,
            "narrative_strength": stmt.excluded.narrative_strength,
            "narrative_direction": stmt.excluded.narrative_direction,
            "political_score": stmt.excluded.political_score,
        },
    )
    db.execute(stmt)
    if commit:
        db.commit()


def compute_and_store(db: Session, *, commit: bool = True) -> dict:
    """Compute political signal and store it.

    Returns the computed signal dict.
    """
    signal = compute_political_signal(db)
    upsert_signal(db, signal, commit=commit)
    logger.info(
        "Political signal computed: score=%.4f, news_1h=%d, narrative=%s",
        float(signal["political_score"]),
        signal["news_volume_1h"],
        signal.get("dominant_narrative"),
    )
    return signal
