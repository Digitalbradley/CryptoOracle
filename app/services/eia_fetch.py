"""EIA (Energy Information Administration) oil inventory ingestion.

Fetches weekly US crude oil inventory data from EIA API v2.
Series: PET.WCESTUS1.W (weekly ending stocks of crude oil).
Free, API key required. Rate limit: 9000 requests/hour.

Computes week-over-week inventory change and stores to oil_data table.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.macro_liquidity import OilData

logger = logging.getLogger(__name__)

EIA_BASE = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
SERIES_ID = "WCESTUS1"  # Weekly ending stocks, crude oil, US total


def is_available() -> bool:
    """Check if EIA API key is configured."""
    return bool(settings.eia_api_key)


def _fetch_inventory(*, length: int = 104) -> list[dict]:
    """Fetch weekly crude oil inventory from EIA API v2.

    Returns list of dicts with period (date) and value (thousands of barrels).
    Oldest first.
    """
    params = {
        "api_key": settings.eia_api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[product][]": "EPC0",
        "facets[process][]": "SAE",
        "facets[series][]": SERIES_ID,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": str(length),
    }
    try:
        resp = httpx.get(EIA_BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", {}).get("data", [])
    except Exception:
        logger.exception("EIA crude inventory fetch failed")
        return []


def _to_decimal(val) -> Decimal | None:
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def fetch_and_store(db: Session, *, length: int = 104) -> dict:
    """Fetch EIA weekly crude inventory and store to oil_data.

    Computes week-over-week inventory_change.
    Returns summary dict.
    """
    if not is_available():
        logger.warning("EIA API key not configured — skipping oil inventory fetch")
        return {}

    rows = _fetch_inventory(length=length)
    if not rows:
        logger.warning("No EIA inventory data returned")
        return {}

    count = 0
    prev_value: Decimal | None = None

    for row in rows:
        period = row.get("period", "")
        value = _to_decimal(row.get("value"))
        if not period or value is None:
            continue

        ts = datetime.strptime(period[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)

        data: dict = {
            "timestamp": ts,
            "crude_inventory": value,
        }

        # Compute week-over-week change
        if prev_value is not None:
            data["inventory_change"] = value - prev_value
        prev_value = value

        stmt = pg_insert(OilData).values([data])
        update_cols = {k: getattr(stmt.excluded, k) for k in data if k != "timestamp"}
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_=update_cols,
        )
        db.execute(stmt)
        count += 1

    db.commit()
    logger.info("EIA inventory fetch complete: %d oil_data rows updated", count)
    return {"oil_data_inventory": count}


def fetch_latest(db: Session) -> dict:
    """Fetch last 8 weeks for scheduled updates."""
    return fetch_and_store(db, length=8)
