"""Numerology, Gematria, and Custom Cycles API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.gematria_values import GematriaValues
from app.models.numerology_daily import NumerologyDaily
from app.services import cycle_tracker
from app.services.numerology_compute import GematriaCalculator
from app.signals.numerology import compute_daily_numerology

router = APIRouter(tags=["numerology"])


def _numerology_to_dict(row: NumerologyDaily) -> dict:
    """Convert a NumerologyDaily row to a JSON-serializable dict."""
    return {
        "date": row.date.isoformat(),
        "date_digit_sum": row.date_digit_sum,
        "is_master_number": row.is_master_number,
        "master_number_value": row.master_number_value,
        "universal_day_number": row.universal_day_number,
        "active_cycles": row.active_cycles,
        "cycle_confluence_count": row.cycle_confluence_count,
        "price_47_appearances": row.price_47_appearances,
        "numerology_score": str(row.numerology_score) if row.numerology_score is not None else None,
    }


# ---- Numerology endpoints ----

@router.get("/api/numerology/current")
def get_current_numerology(db: Session = Depends(get_db)):
    """Get today's numerology (compute if not cached)."""
    today = date.today()

    row = db.execute(
        select(NumerologyDaily).where(NumerologyDaily.date == today)
    ).scalar_one_or_none()

    if row is None:
        result = compute_daily_numerology(today, db)
        # Convert date for JSON
        result["date"] = result["date"].isoformat()
        return {"date": today.isoformat(), "numerology": result}

    return {"date": today.isoformat(), "numerology": _numerology_to_dict(row)}


@router.get("/api/numerology/{target_date}")
def get_numerology_by_date(target_date: date, db: Session = Depends(get_db)):
    """Get numerology for a specific date (compute if not cached)."""
    row = db.execute(
        select(NumerologyDaily).where(NumerologyDaily.date == target_date)
    ).scalar_one_or_none()

    if row is None:
        result = compute_daily_numerology(target_date, db)
        result["date"] = result["date"].isoformat()
        return {"date": target_date.isoformat(), "numerology": result}

    return {"date": target_date.isoformat(), "numerology": _numerology_to_dict(row)}


# ---- Gematria endpoints ----

@router.get("/api/gematria/calculate")
def calculate_gematria(
    text: str = Query(..., description="Text to compute gematria for"),
):
    """Compute gematria values for arbitrary text (no DB storage)."""
    calc = GematriaCalculator()
    values = calc.calculate_all_ciphers(text)
    return {"text": text, "values": values}


@router.get("/api/gematria/{term}")
def get_gematria_term(term: str, db: Session = Depends(get_db)):
    """Get stored gematria values for a known term, or compute on-the-fly."""
    row = db.execute(
        select(GematriaValues).where(GematriaValues.term == term)
    ).scalar_one_or_none()

    if row is not None:
        return {
            "term": row.term,
            "stored": True,
            "values": {
                "english_ordinal": row.english_ordinal,
                "full_reduction": row.full_reduction,
                "reverse_ordinal": row.reverse_ordinal,
                "reverse_reduction": row.reverse_reduction,
                "jewish_gematria": row.jewish_gematria,
                "english_gematria": row.english_gematria,
            },
            "digit_sum": row.digit_sum,
            "is_prime": row.is_prime,
            "associated_planet": row.associated_planet,
            "associated_element": row.associated_element,
            "notes": row.notes,
        }

    # Compute on-the-fly
    calc = GematriaCalculator()
    values = calc.calculate_all_ciphers(term)
    return {"term": term, "stored": False, "values": values}


# ---- Cycle endpoints ----

@router.get("/api/cycles")
def list_cycles(db: Session = Depends(get_db)):
    """List all active custom cycles with stats."""
    cycles = cycle_tracker.get_all_active(db)
    return {"count": len(cycles), "cycles": cycles}


@router.get("/api/cycles/check/{target_date}")
def check_cycles_for_date(target_date: date, db: Session = Depends(get_db)):
    """Check which cycles align with a given date."""
    alignments = cycle_tracker.check_date(db, target_date)
    active = [a for a in alignments if a["is_aligned"]]
    return {
        "date": target_date.isoformat(),
        "total_cycles": len(alignments),
        "aligned_count": len(active),
        "alignments": alignments,
    }
