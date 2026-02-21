"""Celestial state API endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.celestial_state import CelestialState
from app.signals.celestial import CelestialEngine

router = APIRouter(prefix="/api/celestial", tags=["celestial"])


def _state_to_dict(row: CelestialState) -> dict:
    """Convert a CelestialState row to a JSON-serializable dict."""
    return {
        "timestamp": row.timestamp.isoformat(),
        "lunar_phase_angle": str(row.lunar_phase_angle) if row.lunar_phase_angle else None,
        "lunar_phase_name": row.lunar_phase_name,
        "lunar_illumination": str(row.lunar_illumination) if row.lunar_illumination else None,
        "days_to_next_new_moon": str(row.days_to_next_new_moon) if row.days_to_next_new_moon else None,
        "days_to_next_full_moon": str(row.days_to_next_full_moon) if row.days_to_next_full_moon else None,
        "is_lunar_eclipse": row.is_lunar_eclipse,
        "is_solar_eclipse": row.is_solar_eclipse,
        "mercury_retrograde": row.mercury_retrograde,
        "venus_retrograde": row.venus_retrograde,
        "mars_retrograde": row.mars_retrograde,
        "jupiter_retrograde": row.jupiter_retrograde,
        "saturn_retrograde": row.saturn_retrograde,
        "retrograde_count": row.retrograde_count,
        "sun_longitude": str(row.sun_longitude) if row.sun_longitude else None,
        "moon_longitude": str(row.moon_longitude) if row.moon_longitude else None,
        "mercury_longitude": str(row.mercury_longitude) if row.mercury_longitude else None,
        "venus_longitude": str(row.venus_longitude) if row.venus_longitude else None,
        "mars_longitude": str(row.mars_longitude) if row.mars_longitude else None,
        "jupiter_longitude": str(row.jupiter_longitude) if row.jupiter_longitude else None,
        "saturn_longitude": str(row.saturn_longitude) if row.saturn_longitude else None,
        "active_aspects": row.active_aspects,
        "ingresses": row.ingresses,
        "celestial_score": str(row.celestial_score) if row.celestial_score else None,
    }


@router.get("/current")
def get_current_celestial(db: Session = Depends(get_db)):
    """Get today's celestial state (compute if not cached)."""
    today = date.today()
    today_dt = datetime(today.year, today.month, today.day)

    row = db.execute(
        select(CelestialState).where(CelestialState.timestamp == today_dt)
    ).scalar_one_or_none()

    if row is None:
        # Compute on-the-fly
        engine = CelestialEngine()
        state = engine.compute_daily_state(today, db)
        return {"date": today.isoformat(), "state": state}

    return {"date": today.isoformat(), "state": _state_to_dict(row)}


@router.get("/history")
def get_celestial_history(
    start: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get historical celestial state within a date range."""
    stmt = select(CelestialState)
    if start:
        stmt = stmt.where(CelestialState.timestamp >= datetime(start.year, start.month, start.day))
    if end:
        stmt = stmt.where(CelestialState.timestamp <= datetime(end.year, end.month, end.day))
    stmt = stmt.order_by(CelestialState.timestamp.desc()).limit(limit)

    rows = db.execute(stmt).scalars().all()
    return {
        "count": len(rows),
        "states": [_state_to_dict(r) for r in reversed(rows)],
    }


@router.get("/{target_date}")
def get_celestial_by_date(
    target_date: date,
    db: Session = Depends(get_db),
):
    """Get celestial state for a specific date (compute if not cached)."""
    dt = datetime(target_date.year, target_date.month, target_date.day)

    row = db.execute(
        select(CelestialState).where(CelestialState.timestamp == dt)
    ).scalar_one_or_none()

    if row is None:
        engine = CelestialEngine()
        state = engine.compute_daily_state(target_date, db)
        return {"date": target_date.isoformat(), "state": state}

    return {"date": target_date.isoformat(), "state": _state_to_dict(row)}
