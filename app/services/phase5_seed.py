"""Phase 5 bootstrap — Macro Liquidity (Layer 7) initialization.

Per brief Section 8.1 priority order:
1. FRED backfill (1 year)
2. Forex fetch
3. CFTC 52 weeks
4. EIA inventory
5. Create/update weight profile (brief Section 7.1 weights)
6. Seed new calendar events (BOJ, ECB, OPEC, Treasury)
7. Compute initial signal
"""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.signal_weights import SignalWeights

logger = logging.getLogger(__name__)


def backfill_fred(db: Session) -> dict:
    """Backfill 1 year of FRED data."""
    from app.services.fred_fetch import fetch_and_store_all, is_available

    if not is_available():
        logger.warning("FRED API key not configured — skipping backfill")
        return {"fred": "skipped (no API key)"}

    result = fetch_and_store_all(db, lookback_days=400)
    logger.info("FRED backfill complete: %s", result)
    return {"fred": result}


def backfill_forex(db: Session) -> dict:
    """Backfill 90 days of forex data."""
    from app.services.forex_fetch import fetch_and_store, is_available

    if not is_available():
        logger.warning("Twelve Data API key not configured — skipping forex backfill")
        return {"forex": "skipped (no API key)"}

    result = fetch_and_store(db, outputsize=90)
    logger.info("Forex backfill complete: %s", result)
    return {"forex": result}


def backfill_cftc(db: Session) -> dict:
    """Backfill 52 weeks of CFTC COT data."""
    from app.services.cftc_fetch import fetch_and_store

    result = fetch_and_store(db, limit=104)
    logger.info("CFTC backfill complete: %s", result)
    return {"cftc": result}


def backfill_eia(db: Session) -> dict:
    """Backfill 2 years of EIA inventory data."""
    from app.services.eia_fetch import fetch_and_store, is_available

    if not is_available():
        logger.warning("EIA API key not configured — skipping inventory backfill")
        return {"eia": "skipped (no API key)"}

    result = fetch_and_store(db, length=104)
    logger.info("EIA backfill complete: %s", result)
    return {"eia": result}


def update_weight_profile(db: Session) -> dict:
    """Create/update weight profile with brief Section 7.1 defaults."""
    # Check if an active profile exists
    existing = db.execute(
        select(SignalWeights).where(SignalWeights.is_active.is_(True))
    ).scalar_one_or_none()

    if existing:
        # Only update macro_weight if it's still at default 0.00
        if float(existing.macro_weight) == 0.0:
            existing.ta_weight = Decimal("0.20")
            existing.onchain_weight = Decimal("0.15")
            existing.celestial_weight = Decimal("0.12")
            existing.numerology_weight = Decimal("0.08")
            existing.sentiment_weight = Decimal("0.12")
            existing.political_weight = Decimal("0.13")
            existing.macro_weight = Decimal("0.20")
            db.commit()
            logger.info("Updated existing weight profile with Layer 7 defaults")
            return {"weights": "updated"}
        logger.info("Weight profile already includes macro — skipping")
        return {"weights": "already_configured"}

    # Create new profile
    profile = SignalWeights(
        profile_name="default_7layer",
        ta_weight=Decimal("0.20"),
        onchain_weight=Decimal("0.15"),
        celestial_weight=Decimal("0.12"),
        numerology_weight=Decimal("0.08"),
        sentiment_weight=Decimal("0.12"),
        political_weight=Decimal("0.13"),
        macro_weight=Decimal("0.20"),
        is_active=True,
    )
    db.add(profile)
    db.commit()
    logger.info("Created new 7-layer weight profile")
    return {"weights": "created"}


def seed_macro_calendar(db: Session) -> dict:
    """Re-seed calendar to include BOJ/ECB/OPEC/Treasury events."""
    from app.services.political_calendar_service import seed_recurring_events

    count = seed_recurring_events(db, year=2026)
    logger.info("Calendar re-seeded with macro events: %d total", count)
    return {"calendar_events": count}


def compute_initial_signal(db: Session) -> dict:
    """Compute the first macro liquidity signal."""
    from app.services.macro_signal_service import compute_macro_signal

    try:
        result = compute_macro_signal(db)
        logger.info(
            "Initial macro signal: score=%.4f regime=%s",
            result["macro_score"],
            result["regime"],
        )
        return {"macro_signal": result["macro_score"], "regime": result["regime"]}
    except Exception:
        logger.exception("Error computing initial macro signal")
        return {"macro_signal": "error"}


def run_phase5_bootstrap(db: Session) -> dict:
    """Run full Phase 5 bootstrap in order."""
    logger.info("=== Phase 5 Bootstrap: Macro Liquidity (Layer 7) ===")
    results = {}

    results.update(backfill_fred(db))
    results.update(backfill_forex(db))
    results.update(backfill_cftc(db))
    results.update(backfill_eia(db))
    results.update(update_weight_profile(db))
    results.update(seed_macro_calendar(db))
    results.update(compute_initial_signal(db))

    logger.info("=== Phase 5 Bootstrap Complete ===")
    return results
