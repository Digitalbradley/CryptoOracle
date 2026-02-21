"""CCXT-based OHLCV data ingestion service.

Fetches historical and live candle data from Binance (public API)
and upserts into the price_data table.
"""

import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

import ccxt
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.price_data import PriceData

logger = logging.getLogger(__name__)

# Binance public API — no keys required for OHLCV
_exchange = ccxt.binance({"enableRateLimit": True})

DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "XRP/USDT"]
DEFAULT_TIMEFRAMES = ["1h", "4h", "1d"]
BACKFILL_START = datetime(2020, 1, 1, tzinfo=timezone.utc)
PAGE_SIZE = 1000
PAGE_SLEEP = 1.0  # seconds between pagination requests


def fetch_ohlcv(
    symbol: str,
    timeframe: str,
    since: int | None = None,
    limit: int = PAGE_SIZE,
) -> list[list]:
    """Fetch OHLCV candles from Binance.

    Args:
        symbol: Trading pair, e.g. "BTC/USDT"
        timeframe: Candle interval, e.g. "1h", "4h", "1d"
        since: Start timestamp in milliseconds (UTC)
        limit: Max candles per request (Binance max: 1000)

    Returns:
        List of [timestamp_ms, open, high, low, close, volume]
    """
    return _exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)


def upsert_candles(
    db: Session,
    candles: list[list],
    symbol: str,
    exchange: str,
    timeframe: str,
) -> int:
    """Upsert OHLCV candles into price_data using ON CONFLICT DO UPDATE.

    Args:
        db: SQLAlchemy session
        candles: CCXT-format candle rows
        symbol: Trading pair
        exchange: Exchange name
        timeframe: Candle interval

    Returns:
        Number of rows upserted
    """
    if not candles:
        return 0

    rows = []
    for c in candles:
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc),
                "symbol": symbol,
                "exchange": exchange,
                "timeframe": timeframe,
                "open": Decimal(str(c[1])),
                "high": Decimal(str(c[2])),
                "low": Decimal(str(c[3])),
                "close": Decimal(str(c[4])),
                "volume": Decimal(str(c[5])),
            }
        )

    stmt = pg_insert(PriceData).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["timestamp", "symbol", "exchange", "timeframe"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
        },
    )
    db.execute(stmt)
    db.commit()
    return len(rows)


def backfill(
    db: Session,
    symbol: str,
    timeframe: str,
    exchange: str = "binance",
    start_date: datetime | None = None,
) -> int:
    """Paginated historical backfill for a single symbol + timeframe.

    Fetches 1000 candles per page, sleeping between requests to respect
    rate limits. Continues until no more data is returned.

    Returns:
        Total number of candles ingested
    """
    since_dt = start_date or BACKFILL_START
    since_ms = int(since_dt.timestamp() * 1000)
    total = 0

    logger.info("Backfill %s %s from %s", symbol, timeframe, since_dt.isoformat())

    while True:
        candles = fetch_ohlcv(symbol, timeframe, since=since_ms, limit=PAGE_SIZE)
        if not candles:
            break

        count = upsert_candles(db, candles, symbol, exchange, timeframe)
        total += count

        logger.info(
            "  %s %s: +%d candles (total %d), last=%s",
            symbol,
            timeframe,
            count,
            total,
            datetime.fromtimestamp(candles[-1][0] / 1000, tz=timezone.utc).isoformat(),
        )

        # If we got fewer candles than requested, we've caught up
        if len(candles) < PAGE_SIZE:
            break

        # Advance past the last candle
        since_ms = candles[-1][0] + 1
        time.sleep(PAGE_SLEEP)

    logger.info("Backfill complete: %s %s — %d candles total", symbol, timeframe, total)
    return total


def fetch_latest(
    db: Session,
    symbol: str,
    timeframe: str,
    exchange: str = "binance",
    limit: int = 5,
) -> int:
    """Fetch the most recent candles and upsert (for hourly updates).

    Returns:
        Number of candles upserted
    """
    candles = fetch_ohlcv(symbol, timeframe, limit=limit)
    return upsert_candles(db, candles, symbol, exchange, timeframe)
