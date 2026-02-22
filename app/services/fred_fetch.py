"""FRED (Federal Reserve Economic Data) ingestion service.

Fetches ~60% of Layer 7 macro data from the St. Louis Fed FRED API:
  - Liquidity: M2SL, WALCL, DFF, WTREGEN, RRPONTSYD
  - Rates:     DGS2, DGS10, DFII10, T5YIE, CPIAUCSL
  - Prices:    DTWEXBGS (DXY proxy), VIXCLS
  - Oil:       DCOILWTICO, DCOILBRENTEU

FRED returns "." for missing observations — these are filtered out.
Rate limit: 120 requests/minute (generous).
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.macro_liquidity import (
    LiquidityData,
    MacroPrices,
    OilData,
    RateData,
)

logger = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# ---------- Series → table mapping ----------

# Each entry: (series_id, target_table_model, column_name)
LIQUIDITY_SERIES = [
    ("M2SL", "m2_supply"),
    ("WALCL", "fed_balance_sheet"),
    ("DFF", "fed_funds_rate"),
    ("WTREGEN", "treasury_general_acct"),
    ("RRPONTSYD", "reverse_repo"),
]

RATE_SERIES = [
    ("DGS2", "dgs2"),
    ("DGS10", "dgs10"),
    ("DFII10", "dfii10"),
    ("T5YIE", "t5yie"),
    ("CPIAUCSL", "cpi_yoy"),  # special handling: compute YoY pct
]

PRICE_SERIES = [
    ("DTWEXBGS", "dxy_index"),
    ("VIXCLS", "vix"),
]

OIL_SERIES = [
    ("DCOILWTICO", "wti_price"),
    ("DCOILBRENTEU", "brent_price"),
]


def is_available() -> bool:
    """Check if FRED API key is configured."""
    return bool(settings.fred_api_key)


# ---------- Low-level fetcher ----------


def _fetch_series(
    series_id: str,
    *,
    lookback_days: int = 400,
) -> list[dict]:
    """Fetch a single FRED series.

    Returns list of {"date": "YYYY-MM-DD", "value": str} dicts.
    Filters out FRED's "." placeholder for missing data.
    """
    start = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime(
        "%Y-%m-%d"
    )
    params = {
        "series_id": series_id,
        "api_key": settings.fred_api_key,
        "file_type": "json",
        "observation_start": start,
        "sort_order": "asc",
    }
    try:
        resp = httpx.get(FRED_BASE, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        obs = data.get("observations", [])
        # Filter FRED "." placeholder for missing values
        return [o for o in obs if o.get("value") not in (".", "", None)]
    except Exception:
        logger.exception("FRED fetch failed for series %s", series_id)
        return []


def _to_decimal(val: str) -> Decimal | None:
    """Parse FRED string value to Decimal."""
    try:
        return Decimal(val)
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_date(date_str: str) -> datetime:
    """Parse FRED 'YYYY-MM-DD' to datetime."""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


# ---------- Table upserts ----------


def _upsert_liquidity(db: Session, series_id: str, column: str, obs: list[dict]) -> int:
    """Upsert FRED observations into liquidity_data, also computing net_liquidity."""
    count = 0
    for o in obs:
        ts = _parse_date(o["date"])
        val = _to_decimal(o["value"])
        if val is None:
            continue
        row = {"timestamp": ts, column: val}
        stmt = pg_insert(LiquidityData).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_={column: val},
        )
        db.execute(stmt)
        count += 1
    return count


def _upsert_rates(db: Session, series_id: str, column: str, obs: list[dict]) -> int:
    """Upsert FRED observations into rate_data."""
    count = 0
    for o in obs:
        ts = _parse_date(o["date"])
        val = _to_decimal(o["value"])
        if val is None:
            continue
        row = {"timestamp": ts, column: val}
        stmt = pg_insert(RateData).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_={column: val},
        )
        db.execute(stmt)
        count += 1
    return count


def _upsert_prices(db: Session, series_id: str, column: str, obs: list[dict]) -> int:
    """Upsert FRED observations into macro_prices."""
    count = 0
    for o in obs:
        ts = _parse_date(o["date"])
        val = _to_decimal(o["value"])
        if val is None:
            continue
        row = {"timestamp": ts, column: val}
        stmt = pg_insert(MacroPrices).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_={column: val},
        )
        db.execute(stmt)
        count += 1
    return count


def _upsert_oil(db: Session, series_id: str, column: str, obs: list[dict]) -> int:
    """Upsert FRED observations into oil_data."""
    count = 0
    for o in obs:
        ts = _parse_date(o["date"])
        val = _to_decimal(o["value"])
        if val is None:
            continue
        row = {"timestamp": ts, column: val}
        stmt = pg_insert(OilData).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_={column: val},
        )
        db.execute(stmt)
        count += 1
    return count


# ---------- CPI YoY computation ----------


def _compute_cpi_yoy(db: Session, obs: list[dict]) -> int:
    """Compute CPI YoY percentage change and store in rate_data.cpi_yoy.

    FRED CPIAUCSL is the index level; we need the year-over-year percentage.
    """
    if len(obs) < 13:
        return 0
    # Build date→value map
    values = {}
    for o in obs:
        val = _to_decimal(o["value"])
        if val is not None and val > 0:
            values[o["date"]] = val

    count = 0
    sorted_dates = sorted(values.keys())
    for date_str in sorted_dates:
        ts = _parse_date(date_str)
        # Find the value ~12 months ago
        target = ts - timedelta(days=365)
        # Find closest date in our data
        closest = None
        for d in sorted_dates:
            d_dt = _parse_date(d)
            if abs((d_dt - target).days) < 45:
                closest = d
                break
        if closest is None:
            continue

        current = values[date_str]
        prior = values[closest]
        yoy_pct = ((current - prior) / prior) * 100

        row = {"timestamp": ts, "cpi_yoy": yoy_pct}
        stmt = pg_insert(RateData).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_={"cpi_yoy": yoy_pct},
        )
        db.execute(stmt)
        count += 1
    return count


# ---------- Net liquidity computation ----------


def compute_net_liquidity(db: Session) -> int:
    """Compute net_liquidity = fed_balance_sheet - TGA - reverse_repo.

    Updates existing liquidity_data rows where all three components exist.
    """
    from sqlalchemy import text

    sql = text("""
        UPDATE liquidity_data
        SET net_liquidity = fed_balance_sheet - COALESCE(treasury_general_acct, 0)
                            - COALESCE(reverse_repo, 0)
        WHERE fed_balance_sheet IS NOT NULL
          AND (net_liquidity IS NULL
               OR net_liquidity != fed_balance_sheet
                                   - COALESCE(treasury_general_acct, 0)
                                   - COALESCE(reverse_repo, 0))
    """)
    result = db.execute(sql)
    return result.rowcount


# ---------- Yield curve computation ----------


def compute_yield_curve(db: Session) -> int:
    """Compute yield_curve_2s10s = dgs10 - dgs2 for rate_data rows."""
    from sqlalchemy import text

    sql = text("""
        UPDATE rate_data
        SET yield_curve_2s10s = dgs10 - dgs2
        WHERE dgs10 IS NOT NULL
          AND dgs2 IS NOT NULL
          AND (yield_curve_2s10s IS NULL
               OR yield_curve_2s10s != dgs10 - dgs2)
    """)
    result = db.execute(sql)
    return result.rowcount


# ---------- WTI-Brent spread ----------


def compute_oil_spread(db: Session) -> int:
    """Compute wti_brent_spread = wti_price - brent_price."""
    from sqlalchemy import text

    sql = text("""
        UPDATE oil_data
        SET wti_brent_spread = wti_price - brent_price
        WHERE wti_price IS NOT NULL
          AND brent_price IS NOT NULL
          AND (wti_brent_spread IS NULL
               OR wti_brent_spread != wti_price - brent_price)
    """)
    result = db.execute(sql)
    return result.rowcount


# ---------- Main entry points ----------


def fetch_and_store_all(db: Session, *, lookback_days: int = 400) -> dict:
    """Fetch all FRED series and store to their respective tables.

    Returns summary dict with row counts per table.
    """
    if not is_available():
        logger.warning("FRED API key not configured — skipping macro data fetch")
        return {}

    summary: dict[str, int] = {}

    # Liquidity series
    liq_total = 0
    for series_id, column in LIQUIDITY_SERIES:
        obs = _fetch_series(series_id, lookback_days=lookback_days)
        n = _upsert_liquidity(db, series_id, column, obs)
        liq_total += n
        logger.info("FRED %s → liquidity_data.%s: %d rows", series_id, column, n)
    summary["liquidity_data"] = liq_total

    # Rate series (CPI handled specially)
    rate_total = 0
    for series_id, column in RATE_SERIES:
        obs = _fetch_series(series_id, lookback_days=lookback_days)
        if series_id == "CPIAUCSL":
            n = _compute_cpi_yoy(db, obs)
        else:
            n = _upsert_rates(db, series_id, column, obs)
        rate_total += n
        logger.info("FRED %s → rate_data.%s: %d rows", series_id, column, n)
    summary["rate_data"] = rate_total

    # Price series (DXY proxy + VIX)
    price_total = 0
    for series_id, column in PRICE_SERIES:
        obs = _fetch_series(series_id, lookback_days=lookback_days)
        n = _upsert_prices(db, series_id, column, obs)
        price_total += n
        logger.info("FRED %s → macro_prices.%s: %d rows", series_id, column, n)
    summary["macro_prices"] = price_total

    # Oil series
    oil_total = 0
    for series_id, column in OIL_SERIES:
        obs = _fetch_series(series_id, lookback_days=lookback_days)
        n = _upsert_oil(db, series_id, column, obs)
        oil_total += n
        logger.info("FRED %s → oil_data.%s: %d rows", series_id, column, n)
    summary["oil_data"] = oil_total

    # Computed columns
    n = compute_net_liquidity(db)
    logger.info("Computed net_liquidity for %d rows", n)
    n = compute_yield_curve(db)
    logger.info("Computed yield_curve_2s10s for %d rows", n)
    n = compute_oil_spread(db)
    logger.info("Computed wti_brent_spread for %d rows", n)

    db.commit()
    logger.info("FRED fetch complete: %s", summary)
    return summary


def fetch_latest(db: Session) -> dict:
    """Fetch only the most recent data (last 14 days) for scheduled updates."""
    return fetch_and_store_all(db, lookback_days=14)
