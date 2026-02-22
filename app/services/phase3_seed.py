"""Phase 3 bootstrap — seed weights, backfill sentiment, compute confluence, run backtest.

Orchestrates all Phase 3 initialization:
1. Seed default signal weight profile
2. Backfill Fear & Greed sentiment data (up to 2 years)
3. Compute historical confluence scores
4. Run initial 47-day cycle backtest
"""

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.signal_weights import SignalWeights
from app.models.ta_indicators import TAIndicators
from app.services.backtester import CycleBacktester
from app.services.confluence_engine import ConfluenceEngine, DEFAULT_WEIGHTS
from app.services.sentiment_fetch import (
    compute_sentiment_score,
    fetch_fear_greed_history,
    upsert_sentiment,
)

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "XRP/USDT"]


def seed_default_weights(db: Session) -> bool:
    """Insert default weight profile if not exists.

    Returns:
        True if created, False if already exists.
    """
    existing = db.execute(
        select(SignalWeights).where(
            SignalWeights.profile_name == "default",
            SignalWeights.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if existing:
        logger.info("Default weight profile already exists")
        return False

    profile = SignalWeights(
        profile_name="default",
        ta_weight=Decimal("0.2500"),
        onchain_weight=Decimal("0.2000"),
        celestial_weight=Decimal("0.1500"),
        numerology_weight=Decimal("0.1000"),
        sentiment_weight=Decimal("0.1500"),
        political_weight=Decimal("0.1500"),
        is_active=True,
    )
    db.add(profile)
    db.commit()
    logger.info("Default weight profile created")
    return True


def backfill_sentiment(db: Session, days: int = 730) -> int:
    """Backfill Fear & Greed history from Alternative.me.

    Fetches up to `days` of historical data and stores for all symbols.

    Returns:
        Total rows upserted across all symbols.
    """
    logger.info("Backfilling sentiment data (%d days)...", days)

    history = fetch_fear_greed_history(days)
    if not history:
        logger.warning("No Fear & Greed history returned")
        return 0

    total = 0
    for symbol in DEFAULT_SYMBOLS:
        for i, fg in enumerate(history):
            upsert_sentiment(db, fg, symbol)
            total += 1

            if (i + 1) % 100 == 0:
                logger.info(
                    "  Sentiment backfill %s: %d/%d",
                    symbol,
                    i + 1,
                    len(history),
                )

    logger.info("Sentiment backfill complete: %d rows across %d symbols", total, len(DEFAULT_SYMBOLS))
    return total


def backfill_confluence(db: Session) -> int:
    """Compute historical confluence scores for dates where TA data exists.

    Uses daily timeframe. Iterates through each date that has TA data
    and computes the confluence score from all available layers.

    Returns:
        Number of confluence scores computed.
    """
    logger.info("Backfilling historical confluence scores...")

    engine = ConfluenceEngine()
    total = 0

    for symbol in DEFAULT_SYMBOLS:
        # Get all dates with TA data for this symbol (1d timeframe)
        ta_rows = db.execute(
            select(TAIndicators)
            .where(
                TAIndicators.symbol == symbol,
                TAIndicators.timeframe == "1d",
            )
            .order_by(TAIndicators.timestamp.asc())
        ).scalars().all()

        for i, ta in enumerate(ta_rows):
            try:
                engine.compute_and_store(
                    db, symbol, "1d", timestamp=ta.timestamp
                )
                total += 1
            except Exception:
                logger.exception(
                    "Error computing confluence for %s at %s",
                    symbol,
                    ta.timestamp,
                )

            if (i + 1) % 100 == 0:
                logger.info(
                    "  Confluence backfill %s: %d/%d",
                    symbol,
                    i + 1,
                    len(ta_rows),
                )

    logger.info("Confluence backfill complete: %d scores", total)
    return total


def run_initial_backtest(db: Session) -> dict:
    """Run the 47-day cycle backtester and return the report.

    Returns:
        Full backtest report dict.
    """
    logger.info("Running initial 47-day cycle backtest...")
    backtester = CycleBacktester()
    report = backtester.generate_report(db, symbol="BTC/USDT", min_magnitude=-10.0)
    logger.info(
        "Backtest complete: %d crashes, significant=%s",
        report["total_crash_events"],
        report["cycle_analysis"]["is_significant"],
    )
    return report


def run_phase3_bootstrap(db: Session) -> dict:
    """Orchestrate all Phase 3 bootstrap operations.

    Returns:
        Summary dict with counts and backtest highlights.
    """
    logger.info("=== Phase 3 Bootstrap Starting ===")

    # 1. Seed default weights
    weights_created = seed_default_weights(db)

    # 2. Backfill sentiment
    sentiment_count = backfill_sentiment(db)

    # 3. Backfill confluence scores
    confluence_count = backfill_confluence(db)

    # 4. Run initial backtest
    backtest_report = run_initial_backtest(db)

    summary = {
        "weights_created": weights_created,
        "sentiment_rows": sentiment_count,
        "confluence_scores": confluence_count,
        "backtest": {
            "total_crashes": backtest_report["total_crash_events"],
            "is_47day_significant": backtest_report["cycle_analysis"]["is_significant"],
            "p_value": backtest_report["cycle_analysis"]["p_value"],
            "conclusion": backtest_report["cycle_analysis"]["conclusion"],
        },
    }

    logger.info("=== Phase 3 Bootstrap Complete ===")
    logger.info("  Weights: %s", "created" if weights_created else "already existed")
    logger.info("  Sentiment rows: %d", sentiment_count)
    logger.info("  Confluence scores: %d", confluence_count)
    logger.info("  Backtest conclusion: %s", backtest_report["cycle_analysis"]["conclusion"])

    return summary
