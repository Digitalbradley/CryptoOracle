"""Bootstrap service — seed symbols, backfill data, detect historical events.

Used for initial setup and can be triggered via POST /api/bootstrap.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.historical_events import HistoricalEvents
from app.models.watched_symbols import WatchedSymbols
from app.services.data_ingest import DEFAULT_SYMBOLS, DEFAULT_TIMEFRAMES, backfill
from app.signals.technical import TechnicalAnalyzer

logger = logging.getLogger(__name__)

# Crash/pump detection thresholds
CRASH_THRESHOLD = -0.15   # 15% drop from rolling high
PUMP_THRESHOLD = 0.20     # 20% rise from rolling low
ROLLING_WINDOW = 7        # days for rolling high/low


def seed_watched_symbols(db: Session) -> list[str]:
    """Insert default watched symbols if they don't already exist.

    Returns:
        List of symbol names that were seeded.
    """
    seeded = []
    for symbol in DEFAULT_SYMBOLS:
        exists = db.execute(
            select(WatchedSymbols).where(WatchedSymbols.symbol == symbol)
        ).scalar_one_or_none()

        if exists is None:
            ws = WatchedSymbols(
                symbol=symbol,
                exchange="kraken",
                is_active=True,
                timeframes=DEFAULT_TIMEFRAMES,
            )
            db.add(ws)
            seeded.append(symbol)
            logger.info("Seeded watched symbol: %s", symbol)

    if seeded:
        db.commit()
    return seeded


def backfill_all(db: Session) -> dict[str, int]:
    """Backfill historical data for all active watched symbols.

    Returns:
        Dict of {symbol/timeframe: candle_count}
    """
    symbols = db.execute(
        select(WatchedSymbols).where(WatchedSymbols.is_active.is_(True))
    ).scalars().all()

    results = {}
    for ws in symbols:
        timeframes = ws.timeframes if isinstance(ws.timeframes, list) else DEFAULT_TIMEFRAMES
        for tf in timeframes:
            key = f"{ws.symbol}/{tf}"
            logger.info("Backfilling %s on %s...", ws.symbol, tf)
            count = backfill(db, ws.symbol, tf, exchange=ws.exchange)
            results[key] = count
            logger.info("Backfilled %s: %d candles", key, count)

    return results


def compute_ta_all(db: Session) -> int:
    """Compute TA indicators for all active symbols and timeframes.

    Returns:
        Number of symbol/timeframe pairs computed.
    """
    analyzer = TechnicalAnalyzer()
    symbols = db.execute(
        select(WatchedSymbols).where(WatchedSymbols.is_active.is_(True))
    ).scalars().all()

    computed = 0
    for ws in symbols:
        timeframes = ws.timeframes if isinstance(ws.timeframes, list) else DEFAULT_TIMEFRAMES
        for tf in timeframes:
            result = analyzer.compute_indicators(ws.symbol, tf, db)
            if result is not None:
                computed += 1

    return computed


def detect_crashes_and_pumps(db: Session, symbol: str) -> int:
    """Scan daily price data to detect historical crashes and pumps.

    A crash is detected when the close drops >15% from the rolling 7-day high.
    A pump is detected when the close rises >20% from the rolling 7-day low.

    Returns:
        Number of events detected and inserted.
    """
    from app.models.price_data import PriceData

    # Load daily candles ordered by timestamp
    stmt = (
        select(PriceData)
        .where(
            PriceData.symbol == symbol,
            PriceData.timeframe == "1d",
        )
        .order_by(PriceData.timestamp.asc())
    )
    rows = db.execute(stmt).scalars().all()

    if len(rows) < ROLLING_WINDOW + 1:
        logger.warning("Not enough daily data for %s to detect events", symbol)
        return 0

    df = pd.DataFrame(
        [
            {
                "timestamp": r.timestamp,
                "close": float(r.close) if r.close else 0,
                "high": float(r.high) if r.high else 0,
                "low": float(r.low) if r.low else 0,
            }
            for r in rows
        ]
    )

    rolling_high = df["high"].rolling(window=ROLLING_WINDOW, min_periods=ROLLING_WINDOW).max()
    rolling_low = df["low"].rolling(window=ROLLING_WINDOW, min_periods=ROLLING_WINDOW).min()

    events = []
    last_crash_ts = None
    last_pump_ts = None

    for i in range(ROLLING_WINDOW, len(df)):
        close = df.iloc[i]["close"]
        ts = df.iloc[i]["timestamp"]
        rh = rolling_high.iloc[i]
        rl = rolling_low.iloc[i]

        # Crash detection
        if rh > 0:
            drop_pct = (close - rh) / rh
            if drop_pct <= CRASH_THRESHOLD:
                days_since = (ts - last_crash_ts).days if last_crash_ts else None
                events.append(
                    HistoricalEvents(
                        timestamp=ts,
                        symbol=symbol,
                        event_type="crash",
                        magnitude_pct=Decimal(str(round(drop_pct * 100, 4))),
                        price_at_event=Decimal(str(close)),
                        days_since_previous_crash=days_since,
                    )
                )
                last_crash_ts = ts

        # Pump detection
        if rl > 0:
            rise_pct = (close - rl) / rl
            if rise_pct >= PUMP_THRESHOLD:
                days_since = (ts - last_pump_ts).days if last_pump_ts else None
                events.append(
                    HistoricalEvents(
                        timestamp=ts,
                        symbol=symbol,
                        event_type="pump",
                        magnitude_pct=Decimal(str(round(rise_pct * 100, 4))),
                        price_at_event=Decimal(str(close)),
                        days_since_previous_pump=days_since,
                    )
                )
                last_pump_ts = ts

    if events:
        db.add_all(events)
        db.commit()
        logger.info("Detected %d crash/pump events for %s", len(events), symbol)

    return len(events)


def run_bootstrap(db: Session) -> dict:
    """Full bootstrap procedure: seed → backfill → compute TA → detect events.

    Returns:
        Summary dict with counts.
    """
    logger.info("=== BOOTSTRAP START ===")

    # 1. Seed watched symbols
    seeded = seed_watched_symbols(db)
    logger.info("Seeded symbols: %s", seeded or "(all already present)")

    # 2. Backfill historical data
    backfill_results = backfill_all(db)
    total_candles = sum(backfill_results.values())
    logger.info("Backfill complete: %d total candles", total_candles)

    # 3. Compute TA indicators
    ta_count = compute_ta_all(db)
    logger.info("TA computed for %d symbol/timeframe pairs", ta_count)

    # 4. Detect crashes and pumps
    total_events = 0
    for symbol in DEFAULT_SYMBOLS:
        count = detect_crashes_and_pumps(db, symbol)
        total_events += count

    logger.info("=== BOOTSTRAP COMPLETE ===")
    return {
        "symbols_seeded": seeded,
        "candles_backfilled": total_candles,
        "ta_computed": ta_count,
        "events_detected": total_events,
        "backfill_detail": backfill_results,
    }
