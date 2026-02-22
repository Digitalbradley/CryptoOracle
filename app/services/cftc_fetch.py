"""CFTC Commitments of Traders (COT) ingestion service.

Fetches JPY futures net positioning from the CFTC Socrata API.
Free, no API key required. Weekly data (Friday release, Tuesday date).

Commodity code 097741 = Japanese Yen futures (CME).
Source: publicreporting.cftc.gov/resource/6dca-aqww.json (disaggregated)
"""

import logging
import statistics
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.macro_liquidity import CarryTradeData

logger = logging.getLogger(__name__)

# CFTC Socrata API — Disaggregated Futures Only report
CFTC_BASE = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
JPY_CODE = "097741"  # Japanese Yen


def _fetch_jpy_positioning(*, limit: int = 104) -> list[dict]:
    """Fetch JPY futures positioning from CFTC Socrata API.

    Returns list of weekly reports, oldest first.
    limit=104 ≈ 2 years of weekly data.
    """
    params = {
        "$where": f"commodity_code='{JPY_CODE}'",
        "$order": "report_date_as_yyyy_mm_dd ASC",
        "$limit": str(limit),
    }
    try:
        resp = httpx.get(CFTC_BASE, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logger.exception("CFTC COT fetch failed")
        return []


def _compute_net_and_zscore(reports: list[dict]) -> list[dict]:
    """Compute net positioning and z-score from COT reports.

    net_position = noncommercial_long - noncommercial_short
    z-score computed against trailing 52 weeks.

    Returns list of dicts with: date, net_position, zscore.
    """
    results = []
    net_positions = []

    for report in reports:
        try:
            date_str = report.get("report_date_as_yyyy_mm_dd", "")
            long_all = int(float(report.get("noncomm_positions_long_all", 0)))
            short_all = int(float(report.get("noncomm_positions_short_all", 0)))
            net = long_all - short_all
            net_positions.append(net)

            # Z-score against trailing 52 weeks
            zscore = None
            window = net_positions[-52:]  # last 52 entries
            if len(window) >= 10:
                mean = statistics.mean(window)
                stdev = statistics.stdev(window)
                if stdev > 0:
                    zscore = (net - mean) / stdev

            results.append({
                "date": date_str,
                "net_position": net,
                "zscore": round(zscore, 4) if zscore is not None else None,
            })
        except (ValueError, KeyError):
            logger.debug("Skipping malformed COT report row")
            continue

    return results


def fetch_and_store(db: Session, *, limit: int = 104) -> dict:
    """Fetch CFTC COT data and update carry_trade_data with positioning info.

    Returns summary dict.
    """
    reports = _fetch_jpy_positioning(limit=limit)
    if not reports:
        logger.warning("No CFTC COT data returned")
        return {}

    processed = _compute_net_and_zscore(reports)

    count = 0
    for entry in processed:
        date_str = entry["date"]
        if not date_str:
            continue
        ts = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)

        data = {"timestamp": ts}
        data["jpy_net_positioning"] = entry["net_position"]
        if entry["zscore"] is not None:
            data["jpy_positioning_zscore"] = Decimal(str(entry["zscore"]))

        stmt = pg_insert(CarryTradeData).values([data])
        update_cols = {k: getattr(stmt.excluded, k) for k in data if k != "timestamp"}
        if update_cols:
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp"],
                set_=update_cols,
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=["timestamp"])
        db.execute(stmt)
        count += 1

    db.commit()
    logger.info("CFTC COT fetch complete: %d carry_trade_data rows updated", count)
    return {"carry_trade_data_positioning": count}


def fetch_latest(db: Session) -> dict:
    """Fetch last 8 weeks of CFTC data for scheduled updates."""
    return fetch_and_store(db, limit=8)
