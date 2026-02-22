"""Phase 4 bootstrap — seed calendar events, fetch initial news, compute signal.

Orchestrates Phase 4 (Political Events Layer) initialization.
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def seed_calendar_events(db: Session) -> int:
    """Seed the political calendar with known 2026 events and enrich with gematria."""
    from app.services.political_calendar_service import seed_recurring_events, enrich_with_gematria
    from sqlalchemy import select
    from app.models.political_calendar import PoliticalCalendar

    count = seed_recurring_events(db, year=2026)

    # Enrich all events with gematria
    rows = db.execute(
        select(PoliticalCalendar).where(PoliticalCalendar.event_title_gematria.is_(None))
    ).scalars().all()

    for row in rows:
        try:
            enrich_with_gematria(db, row.id)
        except Exception:
            logger.exception("Failed to enrich event %d with gematria", row.id)

    logger.info("Seeded %d calendar events (enriched %d with gematria)", count, len(rows))
    return count


def initial_news_fetch(db: Session) -> int:
    """Fetch initial batch of political news from available sources."""
    from app.services.political_news_service import fetch_and_store

    try:
        count = fetch_and_store(db)
        logger.info("Initial news fetch: %d articles", count)
        return count
    except Exception:
        logger.exception("Error during initial news fetch")
        return 0


def compute_initial_signal(db: Session) -> bool:
    """Compute the first political signal."""
    from app.services.political_signal_service import compute_and_store

    try:
        result = compute_and_store(db)
        score = float(result.get("political_score", 0))
        logger.info("Initial political signal computed: score=%.4f", score)
        return True
    except Exception:
        logger.exception("Error computing initial political signal")
        return False


def run_phase4_bootstrap(db: Session) -> dict:
    """Orchestrate full Phase 4 bootstrap.

    Steps:
    1. Seed calendar events with gematria enrichment
    2. Fetch initial news from all available sources
    3. Compute first political signal

    Returns summary dict.
    """
    logger.info("Phase 4 bootstrap starting...")

    calendar_count = seed_calendar_events(db)
    news_count = initial_news_fetch(db)
    signal_computed = compute_initial_signal(db)

    summary = {
        "calendar_events_seeded": calendar_count,
        "news_articles_fetched": news_count,
        "signal_computed": signal_computed,
    }
    logger.info("Phase 4 bootstrap complete: %s", summary)
    return summary
