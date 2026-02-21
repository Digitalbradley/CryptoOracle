"""Layer 3B: Numerology and Gematria signal engine.

Computes universal day numbers, master number detection, custom cycle tracking,
and gematria analysis. Outputs numerology_score in range -1.0 to +1.0.
"""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.numerology_daily import NumerologyDaily
from app.services import cycle_tracker
from app.services.numerology_compute import (
    GematriaCalculator,
    analyze_price_for_significance,
    compute_numerology_score,
    date_digit_sum,
    get_master_number_value,
    is_master_number_date,
    reduce_to_digit,
    universal_day_number,
)

logger = logging.getLogger(__name__)

# Re-export computation functions for backward compatibility
__all__ = [
    "universal_day_number",
    "is_master_number_date",
    "date_digit_sum",
    "CycleTracker",
    "GematriaCalculator",
    "analyze_price_for_significance",
    "compute_daily_numerology",
]


class CycleTracker:
    """Track N-day cycles from reference events (e.g., the 47-day crash cycle).

    Wraps the cycle_tracker service functions with a DB session.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_cycle(
        self, name: str, days: int, reference_date: date, reference_event: str,
        tolerance_days: int = 2,
    ):
        return cycle_tracker.add_cycle(
            self.db, name, days, reference_date, reference_event, tolerance_days,
        )

    def check_date(self, d: date) -> list:
        return cycle_tracker.check_date(self.db, d)

    def days_until_next(self, cycle_name: str, from_date: date | None = None) -> int | None:
        from_date = from_date or date.today()
        return cycle_tracker.days_until_next(self.db, cycle_name, from_date)

    def get_hit_rate(self, cycle_name: str) -> float | None:
        cycles = cycle_tracker.get_all_active(self.db)
        for c in cycles:
            if c["name"] == cycle_name:
                return c["hit_rate"]
        return None


def compute_daily_numerology(d: date, db: Session) -> dict:
    """Compute numerology for a given date and upsert to DB.

    Returns the computed numerology dict.
    """
    udn = universal_day_number(d)
    is_master = is_master_number_date(d)
    master_val = get_master_number_value(d)
    dds = date_digit_sum(d)

    # Check cycle alignments
    alignments = cycle_tracker.check_date(db, d)
    active_alignments = [a for a in alignments if a["is_aligned"]]
    cycle_data = {a["name"]: a for a in alignments}

    # Compute score
    score = compute_numerology_score(udn, is_master, active_alignments)

    result = {
        "date": d,
        "date_digit_sum": dds,
        "is_master_number": is_master,
        "master_number_value": master_val,
        "universal_day_number": udn,
        "active_cycles": cycle_data,
        "cycle_confluence_count": len(active_alignments),
        "numerology_score": score,
    }

    # Upsert to DB
    _upsert_numerology(db, result)

    logger.info(
        "Numerology computed for %s — UDN=%d, master=%s, score=%.4f",
        d.isoformat(), udn, is_master, score,
    )
    return result


def _upsert_numerology(db: Session, data: dict) -> None:
    """Upsert numerology data into numerology_daily table."""
    row = {
        "date": data["date"],
        "date_digit_sum": data["date_digit_sum"],
        "is_master_number": data["is_master_number"],
        "master_number_value": data["master_number_value"],
        "universal_day_number": data["universal_day_number"],
        "active_cycles": data["active_cycles"],
        "cycle_confluence_count": data["cycle_confluence_count"],
        "numerology_score": Decimal(str(data["numerology_score"])),
    }

    update_cols = {k: v for k, v in row.items() if k != "date"}
    stmt = pg_insert(NumerologyDaily).values([row])
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],
        set_=update_cols,
    )
    db.execute(stmt)
    db.commit()
