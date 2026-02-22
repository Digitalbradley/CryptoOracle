"""APScheduler-based scheduled update service.

Hourly: Fetches latest candles, recomputes TA indicators, political signal, confluence scores.
Every 30 minutes: Fetches political news from all available sources.
Every 4 hours: Fetches sentiment (Fear & Greed) and on-chain metrics.
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
    """Fetch latest candles, recompute TA, then compute confluence + alerts.

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

        # Compute political signal (before confluence so it picks up the latest score)
        try:
            from app.services.political_signal_service import compute_and_store as compute_political
            compute_political(db)
        except Exception:
            logger.exception("Error computing political signal")

        # Compute confluence scores and run alert checks
        try:
            from app.services.alert_engine import AlertEngine
            from app.services.confluence_engine import ConfluenceEngine

            confluence = ConfluenceEngine()
            alert_engine = AlertEngine()

            for ws in symbols:
                timeframes = ws.timeframes if isinstance(ws.timeframes, list) else DEFAULT_TIMEFRAMES
                for tf in timeframes:
                    try:
                        result = confluence.compute_and_store(db, ws.symbol, tf)
                        alert_engine.run_all_checks(db, ws.symbol, tf, result)
                    except Exception:
                        logger.exception("Error computing confluence for %s %s", ws.symbol, tf)
        except Exception:
            logger.exception("Error in confluence/alert computation")

        logger.info("Hourly update complete.")
    finally:
        db.close()


def run_sentiment_onchain_update() -> None:
    """Fetch sentiment (Fear & Greed) and on-chain metrics.

    Runs every 4 hours in its own DB session.
    """
    logger.info("Sentiment + on-chain update starting...")
    db = SessionLocal()

    try:
        symbols = db.execute(
            select(WatchedSymbols).where(WatchedSymbols.is_active.is_(True))
        ).scalars().all()

        symbol_list = [ws.symbol for ws in symbols]

        # Sentiment: Fear & Greed (market-wide, stored per symbol)
        try:
            from app.services.sentiment_fetch import fetch_and_store_current
            count = fetch_and_store_current(db, symbol_list)
            logger.info("Sentiment updated: %d rows", count)
        except Exception:
            logger.exception("Error fetching sentiment data")

        # On-chain: CryptoQuant + Glassnode (if keys configured)
        try:
            from app.services.onchain_fetch import fetch_and_store, is_available
            if is_available():
                for symbol in symbol_list:
                    try:
                        fetch_and_store(db, symbol)
                    except Exception:
                        logger.exception("Error fetching on-chain for %s", symbol)
            else:
                logger.debug("No on-chain API keys configured — skipping")
        except Exception:
            logger.exception("Error in on-chain update")

        logger.info("Sentiment + on-chain update complete.")
    finally:
        db.close()


def run_political_news_update() -> None:
    """Fetch political news from all available sources.

    Runs every 30 minutes in its own DB session.
    """
    logger.info("Political news update starting...")
    db = SessionLocal()

    try:
        from app.services.political_news_service import fetch_and_store
        count = fetch_and_store(db)
        logger.info("Political news update complete: %d articles", count)
    except Exception:
        logger.exception("Error in political news update")
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
    """Start the background scheduler with all jobs."""
    global _scheduler
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return

    _scheduler = BackgroundScheduler()

    # Hourly: fetch candles + recompute TA + confluence + alerts
    _scheduler.add_job(
        run_hourly_update,
        "interval",
        hours=1,
        id="hourly_update",
        name="Hourly candle fetch + TA + confluence + alerts",
    )

    # Every 30 minutes: political news fetch
    _scheduler.add_job(
        run_political_news_update,
        "interval",
        minutes=30,
        id="political_news_update",
        name="30-min political news fetch",
    )

    # Every 4 hours: sentiment + on-chain
    _scheduler.add_job(
        run_sentiment_onchain_update,
        "interval",
        hours=4,
        id="sentiment_onchain_update",
        name="4-hourly sentiment + on-chain fetch",
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
    logger.info("Scheduler started — hourly + 30-min + 4-hourly + daily jobs enabled")


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
