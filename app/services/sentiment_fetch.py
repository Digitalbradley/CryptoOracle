"""Sentiment data fetcher — Fear & Greed Index from Alternative.me.

Fetches current and historical Fear & Greed data (free, no API key required).
Computes contrarian sentiment_score in range [-1.0, +1.0].
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.sentiment_data import SentimentData

logger = logging.getLogger(__name__)

# Alternative.me Fear & Greed API (free, no key required)
_BASE_URL = settings.alternative_me_api.rstrip("/")


def fetch_fear_greed_current() -> dict | None:
    """Fetch the current Fear & Greed Index value.

    Returns:
        {"value": int, "label": str, "timestamp": datetime} or None on failure
    """
    try:
        resp = httpx.get(f"{_BASE_URL}/?limit=1&format=json", timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "data" not in data or not data["data"]:
            logger.warning("Fear & Greed API returned empty data")
            return None

        entry = data["data"][0]
        return {
            "value": int(entry["value"]),
            "label": entry["value_classification"],
            "timestamp": datetime.fromtimestamp(
                int(entry["timestamp"]), tz=timezone.utc
            ),
        }
    except Exception:
        logger.exception("Failed to fetch Fear & Greed Index")
        return None


def fetch_fear_greed_history(days: int = 365) -> list[dict]:
    """Fetch historical Fear & Greed data.

    Args:
        days: Number of days of history to fetch (max ~2000)

    Returns:
        List of {"value": int, "label": str, "timestamp": datetime}, oldest first
    """
    try:
        resp = httpx.get(
            f"{_BASE_URL}/?limit={days}&format=json", timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        if "data" not in data:
            return []

        results = []
        for entry in data["data"]:
            results.append(
                {
                    "value": int(entry["value"]),
                    "label": entry["value_classification"],
                    "timestamp": datetime.fromtimestamp(
                        int(entry["timestamp"]), tz=timezone.utc
                    ),
                }
            )

        # API returns newest first — reverse to oldest first
        results.reverse()
        return results
    except Exception:
        logger.exception("Failed to fetch Fear & Greed history")
        return []


def compute_sentiment_score(fear_greed_index: int) -> float:
    """Compute contrarian sentiment score from Fear & Greed Index.

    Contrarian logic: extreme fear = bullish, extreme greed = bearish.

    Args:
        fear_greed_index: 0-100 value from Alternative.me

    Returns:
        Score in range [-1.0, +1.0]
    """
    fg = fear_greed_index

    if fg < 10:
        return 1.0  # Maximum contrarian bullish
    elif fg < 20:
        return 0.8
    elif fg < 30:
        return 0.5
    elif fg < 40:
        return 0.3
    elif fg < 50:
        return 0.1
    elif fg < 60:
        return 0.0  # Neutral
    elif fg < 70:
        return -0.1
    elif fg < 80:
        return -0.3
    elif fg < 90:
        return -0.5
    else:
        return -0.8  # Maximum contrarian bearish


def upsert_sentiment(
    db: Session,
    fg_data: dict,
    symbol: str,
) -> None:
    """Persist Fear & Greed data to sentiment_data table.

    Args:
        db: SQLAlchemy session
        fg_data: {"value": int, "label": str, "timestamp": datetime}
        symbol: Trading pair (F&G is market-wide, stored per watched symbol)
    """
    score = compute_sentiment_score(fg_data["value"])

    row = {
        "timestamp": fg_data["timestamp"],
        "symbol": symbol,
        "fear_greed_index": fg_data["value"],
        "fear_greed_label": fg_data["label"],
        "sentiment_score": Decimal(str(round(score, 4))),
    }

    stmt = pg_insert(SentimentData).values([row])
    stmt = stmt.on_conflict_do_update(
        index_elements=["timestamp", "symbol"],
        set_={
            "fear_greed_index": stmt.excluded.fear_greed_index,
            "fear_greed_label": stmt.excluded.fear_greed_label,
            "sentiment_score": stmt.excluded.sentiment_score,
        },
    )
    db.execute(stmt)
    db.commit()


def fetch_and_store_current(db: Session, symbols: list[str]) -> int:
    """Fetch current Fear & Greed and store for all watched symbols.

    Returns:
        Number of rows upserted (0 if fetch failed)
    """
    fg = fetch_fear_greed_current()
    if fg is None:
        return 0

    for symbol in symbols:
        upsert_sentiment(db, fg, symbol)

    logger.info(
        "Sentiment stored: F&G=%d (%s) for %d symbols",
        fg["value"],
        fg["label"],
        len(symbols),
    )
    return len(symbols)
