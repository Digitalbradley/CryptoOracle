"""Twelve Data forex ingestion service.

Fetches USD/JPY and EUR/USD daily OHLC data, computes carry-trade
technicals (SMA-20, ATR-14, RSI-14) on USD/JPY, and stores to
carry_trade_data table.

Free tier: 800 API calls/day.  Docs: https://twelvedata.com/docs
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import httpx
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.macro_liquidity import CarryTradeData
from app.services.ta_compute import compute_atr, compute_rsi, compute_sma

logger = logging.getLogger(__name__)

TWELVE_DATA_BASE = "https://api.twelvedata.com/time_series"


def is_available() -> bool:
    """Check if Twelve Data API key is configured."""
    return bool(settings.twelve_data_api_key)


def _fetch_forex(symbol: str, *, outputsize: int = 90) -> list[dict]:
    """Fetch daily OHLC for a forex pair from Twelve Data.

    Returns list of dicts with keys: datetime, open, high, low, close.
    Oldest first.
    """
    params = {
        "symbol": symbol,
        "interval": "1day",
        "outputsize": outputsize,
        "apikey": settings.twelve_data_api_key,
        "format": "JSON",
    }
    try:
        resp = httpx.get(TWELVE_DATA_BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if "values" not in data:
            logger.error("Twelve Data returned no values for %s: %s", symbol, data.get("message", ""))
            return []

        # API returns newest first; reverse for chronological order
        return list(reversed(data["values"]))
    except Exception:
        logger.exception("Twelve Data fetch failed for %s", symbol)
        return []


def _to_decimal(val) -> Decimal | None:
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _compute_technicals(bars: list[dict]) -> pd.DataFrame:
    """Compute SMA-20, ATR-14, RSI-14 on USD/JPY bars.

    Returns DataFrame with columns: datetime, close, sma_20, atr_14, rsi_14.
    """
    df = pd.DataFrame(bars)
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["sma_20"] = compute_sma(df["close"], 20)
    df["atr_14"] = compute_atr(df["high"], df["low"], df["close"], 14)
    df["rsi_14"] = compute_rsi(df["close"], 14)

    return df


def fetch_and_store(db: Session, *, outputsize: int = 90) -> dict:
    """Fetch USD/JPY and EUR/USD, compute technicals, store to carry_trade_data.

    Returns summary dict.
    """
    if not is_available():
        logger.warning("Twelve Data API key not configured — skipping forex fetch")
        return {}

    # Fetch both pairs
    usdjpy_bars = _fetch_forex("USD/JPY", outputsize=outputsize)
    eurusd_bars = _fetch_forex("EUR/USD", outputsize=outputsize)

    if not usdjpy_bars:
        logger.warning("No USD/JPY data returned")
        return {}

    # Compute technicals on USD/JPY
    df_jpy = _compute_technicals(usdjpy_bars)

    # Build EUR/USD lookup by date
    eurusd_map: dict[str, Decimal] = {}
    for bar in eurusd_bars:
        val = _to_decimal(bar["close"])
        if val is not None:
            eurusd_map[bar["datetime"]] = val

    count = 0
    for _, row in df_jpy.iterrows():
        date_str = row["datetime"]
        ts = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        usdjpy_val = _to_decimal(row["close"])
        if usdjpy_val is None:
            continue

        data = {
            "timestamp": ts,
            "usdjpy": usdjpy_val,
            "eurusd": eurusd_map.get(date_str),
            "usdjpy_sma_20": _to_decimal(row.get("sma_20")),
            "usdjpy_atr_14": _to_decimal(row.get("atr_14")),
            "usdjpy_rsi_14": _to_decimal(row.get("rsi_14")),
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        data.setdefault("timestamp", ts)

        stmt = pg_insert(CarryTradeData).values([data])
        update_cols = {k: getattr(stmt.excluded, k) for k in data if k != "timestamp"}
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_=update_cols,
        )
        db.execute(stmt)
        count += 1

    db.commit()
    logger.info("Forex fetch complete: %d carry_trade_data rows upserted", count)
    return {"carry_trade_data": count}


def fetch_latest(db: Session) -> dict:
    """Fetch last 30 days of forex data for scheduled updates."""
    return fetch_and_store(db, outputsize=30)
