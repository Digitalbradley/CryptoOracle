"""Custom cycle tracking service.

Tracks N-day cycles from reference events (e.g., the 47-day crash cycle).
Queries the custom_cycles table for active cycles and checks alignment.
"""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.custom_cycles import CustomCycles

logger = logging.getLogger(__name__)


def add_cycle(
    db: Session,
    name: str,
    cycle_days: int,
    reference_date: date,
    reference_event: str | None = None,
    tolerance_days: int = 2,
    notes: str | None = None,
) -> CustomCycles:
    """Create a new custom cycle in the database.

    Returns the created CustomCycles object.
    """
    cycle = CustomCycles(
        name=name,
        cycle_days=cycle_days,
        reference_date=reference_date,
        reference_event=reference_event,
        tolerance_days=tolerance_days,
        notes=notes,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    logger.info("Added cycle: %s (%d days from %s)", name, cycle_days, reference_date)
    return cycle


def check_date(db: Session, target: date) -> list[dict]:
    """Check which active cycles align with the given date (± tolerance).

    Returns list of dicts with cycle info and alignment details.
    """
    cycles = db.execute(
        select(CustomCycles).where(CustomCycles.is_active.is_(True))
    ).scalars().all()

    alignments = []
    for cycle in cycles:
        days_since = (target - cycle.reference_date).days
        if days_since < 0:
            continue

        # How many full cycles have passed?
        cycle_number = days_since // cycle.cycle_days
        day_in_cycle = days_since % cycle.cycle_days
        days_remaining = cycle.cycle_days - day_in_cycle

        # Check if we're within tolerance of a cycle boundary
        is_aligned = (
            day_in_cycle <= cycle.tolerance_days
            or days_remaining <= cycle.tolerance_days
        )

        # Next alignment date
        if day_in_cycle <= cycle.tolerance_days:
            # We're at or near a cycle boundary now
            days_to_next = 0
        else:
            days_to_next = days_remaining

        alignments.append({
            "id": cycle.id,
            "name": cycle.name,
            "cycle_days": cycle.cycle_days,
            "reference_date": cycle.reference_date.isoformat(),
            "reference_event": cycle.reference_event,
            "days_since_reference": days_since,
            "cycle_number": cycle_number + 1,
            "day_in_cycle": day_in_cycle,
            "days_remaining": days_remaining,
            "is_aligned": is_aligned,
            "days_to_next_alignment": days_to_next,
            "tolerance_days": cycle.tolerance_days,
            "hit_rate": float(cycle.hit_rate) if cycle.hit_rate else None,
        })

    return alignments


def days_until_next(db: Session, cycle_name: str, from_date: date) -> int | None:
    """Get days until the next alignment for a named cycle.

    Returns int or None if cycle not found.
    """
    cycle = db.execute(
        select(CustomCycles).where(
            CustomCycles.name == cycle_name,
            CustomCycles.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if cycle is None:
        return None

    days_since = (from_date - cycle.reference_date).days
    if days_since < 0:
        return abs(days_since)

    day_in_cycle = days_since % cycle.cycle_days
    return cycle.cycle_days - day_in_cycle


def record_hit(db: Session, cycle_id: int) -> None:
    """Record a hit for a cycle and update hit_rate."""
    cycle = db.get(CustomCycles, cycle_id)
    if cycle is None:
        return
    cycle.hit_count += 1
    _update_hit_rate(cycle)
    db.commit()


def record_miss(db: Session, cycle_id: int) -> None:
    """Record a miss for a cycle and update hit_rate."""
    cycle = db.get(CustomCycles, cycle_id)
    if cycle is None:
        return
    cycle.miss_count += 1
    _update_hit_rate(cycle)
    db.commit()


def get_all_active(db: Session) -> list[dict]:
    """Get all active cycles with their stats."""
    cycles = db.execute(
        select(CustomCycles).where(CustomCycles.is_active.is_(True))
    ).scalars().all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "cycle_days": c.cycle_days,
            "reference_date": c.reference_date.isoformat(),
            "reference_event": c.reference_event,
            "hit_count": c.hit_count,
            "miss_count": c.miss_count,
            "hit_rate": float(c.hit_rate) if c.hit_rate else None,
            "tolerance_days": c.tolerance_days,
            "notes": c.notes,
        }
        for c in cycles
    ]


def _update_hit_rate(cycle: CustomCycles) -> None:
    """Recalculate hit_rate from hit_count and miss_count."""
    total = cycle.hit_count + cycle.miss_count
    if total > 0:
        cycle.hit_rate = Decimal(str(round(cycle.hit_count / total, 4)))
    else:
        cycle.hit_rate = None
