"""APScheduler-based scheduled update service.

Hourly: Fetches latest candles and recomputes TA indicators.
Daily: Computes celestial state and numerology for the current date.
"""

import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.database import SessionLocal
from app.models.watched_symbols import WatchedSymbols
from app.services.data_ingest import DEFAULT_TIMEFRAMES, fetch_latest
from app.signals.celestial import CelestialEngine
from app.signals.numerology import compute_daily_numerology
from app.signals.technical import TechnicalAnalyzer

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def run_hourly_update() -> None:
    """Fetch latest candles and recompute TA for all active symbols.

    Runs in its own DB session (separate from FastAPI request cycle).
    """
    logger.info("Hourly update starting...")
    db = SessionLocal()
    analyzer = TechnicalAnalyzer()

    try:
        symbols = db.execute(
            select(WatchedSymbols).where(WatchedSymbols.is_active.is_(True))
        ).scalars().all()

        for ws in symbols:
            timeframes = ws.timeframes if isinstance(ws.timeframes, list) else DEFAULT_TIMEFRAMES
            for tf in timeframes:
                try:
                    # Fetch latest candles (last 5)
                    count = fetch_latest(db, ws.symbol, tf, exchange=ws.exchange)
                    logger.info("Fetched %d candles for %s %s", count, ws.symbol, tf)

                    # Recompute TA indicators
                    analyzer.compute_indicators(ws.symbol, tf, db)
                except Exception:
                    logger.exception("Error updating %s %s", ws.symbol, tf)

        logger.info("Hourly update complete.")
    finally:
        db.close()


def run_daily_esoteric() -> None:
    """Compute daily celestial state and numerology.

    Runs in its own DB session. Scheduled at 00:05 UTC daily.
    """
    logger.info("Daily esoteric computation starting...")
    db = SessionLocal()

    try:
        today = date.today()

        # Celestial state
        engine = CelestialEngine()
        engine.compute_daily_state(today, db)
        logger.info("Celestial state computed for %s", today)

        # Numerology
        compute_daily_numerology(today, db)
        logger.info("Numerology computed for %s", today)

        logger.info("Daily esoteric computation complete.")
    except Exception:
        logger.exception("Error in daily esoteric computation")
    finally:
        db.close()


def start_scheduler() -> None:
    """Start the background scheduler with hourly + daily jobs."""
    global _scheduler
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return

    _scheduler = BackgroundScheduler()

    # Hourly: fetch candles + recompute TA
    _scheduler.add_job(
        run_hourly_update,
        "interval",
        hours=1,
        id="hourly_update",
        name="Hourly candle fetch + TA compute",
    )

    # Daily at 00:05 UTC: celestial + numerology
    _scheduler.add_job(
        run_daily_esoteric,
        "cron",
        hour=0,
        minute=5,
        id="daily_esoteric",
        name="Daily celestial + numerology compute",
    )

    _scheduler.start()
    logger.info("Scheduler started — hourly + daily jobs enabled")


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
