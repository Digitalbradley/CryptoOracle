"""Phase 2 bootstrap — seed gematria terms, 47-day cycle, backfill celestial + numerology.

Orchestrates all Phase 2 seeding and backfill operations.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gematria_values import GematriaValues
from app.models.custom_cycles import CustomCycles
from app.services import cycle_tracker
from app.services.numerology_compute import GematriaCalculator, reduce_to_digit, _is_prime
from app.signals.celestial import CelestialEngine
from app.signals.numerology import compute_daily_numerology

logger = logging.getLogger(__name__)

# Crypto-relevant terms for gematria pre-population
SEED_TERMS = [
    "Bitcoin", "Ethereum", "Ripple", "Solana", "Cardano",
    "Satoshi Nakamoto", "blockchain", "cryptocurrency",
    "moon", "crash", "bull", "bear", "halving",
    "whale", "hodl", "defi", "altcoin", "mining",
    "genesis block", "digital gold",
]

BACKFILL_START = date(2020, 1, 1)


def seed_gematria_terms(db: Session) -> int:
    """Pre-populate gematria_values with crypto-relevant terms.

    Returns number of terms seeded.
    """
    calc = GematriaCalculator()
    seeded = 0

    for term in SEED_TERMS:
        exists = db.execute(
            select(GematriaValues).where(GematriaValues.term == term)
        ).scalar_one_or_none()

        if exists is not None:
            continue

        ciphers = calc.calculate_all_ciphers(term)
        ordinal_val = ciphers["english_ordinal"]
        ds = sum(int(d) for d in str(ordinal_val))

        gv = GematriaValues(
            term=term,
            english_ordinal=ciphers["english_ordinal"],
            full_reduction=ciphers["full_reduction"],
            reverse_ordinal=ciphers["reverse_ordinal"],
            reverse_reduction=ciphers["reverse_reduction"],
            jewish_gematria=ciphers["jewish_gematria"],
            english_gematria=ciphers["english_gematria"],
            digit_sum=ds,
            is_prime=_is_prime(ordinal_val),
        )
        db.add(gv)
        seeded += 1
        logger.info("Seeded gematria term: %s (ordinal=%d)", term, ordinal_val)

    if seeded:
        db.commit()
    return seeded


def seed_47_day_cycle(db: Session) -> bool:
    """Create the 47-day crash cycle if it doesn't exist.

    Uses a known BTC crash reference date.

    Returns True if created, False if already exists.
    """
    exists = db.execute(
        select(CustomCycles).where(CustomCycles.name == "47-Day Crash Cycle")
    ).scalar_one_or_none()

    if exists is not None:
        return False

    cycle_tracker.add_cycle(
        db,
        name="47-Day Crash Cycle",
        cycle_days=47,
        reference_date=date(2022, 6, 18),  # BTC crash to ~$17.6k
        reference_event="BTC crash from $31k to $17.6k (Luna/3AC collapse)",
        tolerance_days=2,
        notes="Hypothesized 47-day crash cycle pattern in crypto markets",
    )
    logger.info("Seeded 47-day crash cycle")
    return True


def backfill_celestial(
    db: Session,
    start: date | None = None,
    end: date | None = None,
) -> int:
    """Backfill celestial_state for every day in range.

    Returns number of days computed.
    """
    start = start or BACKFILL_START
    end = end or date.today()
    engine = CelestialEngine()
    count = 0
    current = start

    logger.info("Backfilling celestial data from %s to %s", start, end)

    while current <= end:
        try:
            engine.compute_daily_state(current, db)
            count += 1
            if count % 100 == 0:
                logger.info("  Celestial backfill progress: %d days", count)
        except Exception:
            logger.exception("Error computing celestial for %s", current)

        current += timedelta(days=1)

    logger.info("Celestial backfill complete: %d days", count)
    return count


def backfill_numerology(
    db: Session,
    start: date | None = None,
    end: date | None = None,
) -> int:
    """Backfill numerology_daily for every day in range.

    Returns number of days computed.
    """
    start = start or BACKFILL_START
    end = end or date.today()
    count = 0
    current = start

    logger.info("Backfilling numerology data from %s to %s", start, end)

    while current <= end:
        try:
            compute_daily_numerology(current, db)
            count += 1
            if count % 100 == 0:
                logger.info("  Numerology backfill progress: %d days", count)
        except Exception:
            logger.exception("Error computing numerology for %s", current)

        current += timedelta(days=1)

    logger.info("Numerology backfill complete: %d days", count)
    return count


def cross_reference_events(db: Session) -> int:
    """Enrich historical_events with celestial + numerological state.

    Updates lunar_phase_name, mercury_retrograde, active_aspects_snapshot,
    and date_universal_number for each event.

    Returns number of events updated.
    """
    from app.models.historical_events import HistoricalEvents
    from app.services.celestial_compute import compute_celestial_state
    from app.services.numerology_compute import universal_day_number

    events = db.execute(select(HistoricalEvents)).scalars().all()
    updated = 0

    for event in events:
        try:
            event_date = event.timestamp.date() if hasattr(event.timestamp, 'date') else event.timestamp
            state = compute_celestial_state(event_date)

            event.lunar_phase_name = state["lunar_phase_name"]
            event.mercury_retrograde = state["mercury_retrograde"]
            event.active_aspects_snapshot = state["active_aspects"]
            event.date_universal_number = universal_day_number(event_date)
            updated += 1
        except Exception:
            logger.exception("Error cross-referencing event %d", event.id)

    if updated:
        db.commit()
    logger.info("Cross-referenced %d historical events", updated)
    return updated


def run_phase2_bootstrap(db: Session) -> dict:
    """Full Phase 2 bootstrap: seed terms → seed cycle → backfill celestial → backfill numerology → cross-reference.

    Returns summary dict.
    """
    logger.info("=== PHASE 2 BOOTSTRAP START ===")

    gematria_count = seed_gematria_terms(db)
    logger.info("Seeded %d gematria terms", gematria_count)

    cycle_created = seed_47_day_cycle(db)
    logger.info("47-day cycle: %s", "created" if cycle_created else "already exists")

    celestial_days = backfill_celestial(db)
    numerology_days = backfill_numerology(db)
    events_updated = cross_reference_events(db)

    logger.info("=== PHASE 2 BOOTSTRAP COMPLETE ===")
    return {
        "gematria_terms_seeded": gematria_count,
        "cycle_47_created": cycle_created,
        "celestial_days_computed": celestial_days,
        "numerology_days_computed": numerology_days,
        "events_cross_referenced": events_updated,
    }
