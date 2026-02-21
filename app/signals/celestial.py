"""Layer 3A: Celestial/Astronomical signal engine.

Uses ephem to compute lunar phases, planetary retrogrades,
aspects, eclipses, and ingresses. Outputs celestial_score in range -1.0 to +1.0.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.celestial_state import CelestialState
from app.services.celestial_compute import (
    compute_celestial_score,
    compute_celestial_state,
)

logger = logging.getLogger(__name__)


class CelestialEngine:
    """Compute daily celestial state and score."""

    def compute_daily_state(self, d: date, db: Session) -> dict:
        """Compute full celestial state for a given date and upsert to DB.

        Returns the computed state dict.
        """
        state = compute_celestial_state(d)
        self._upsert_state(db, state)
        logger.info(
            "Celestial state computed for %s — score=%.4f, phase=%s",
            d.isoformat(),
            state.get("celestial_score", 0),
            state.get("lunar_phase_name", ""),
        )
        return state

    def compute_score(self, state: dict) -> float:
        """Compute celestial_score from celestial state."""
        return compute_celestial_score(state)

    def _upsert_state(self, db: Session, state: dict) -> None:
        """Upsert celestial state into the celestial_state table."""
        row = {
            "timestamp": state["timestamp"],
            "lunar_phase_angle": Decimal(str(state["lunar_phase_angle"])),
            "lunar_phase_name": state["lunar_phase_name"],
            "lunar_illumination": Decimal(str(state["lunar_illumination"])),
            "days_to_next_new_moon": Decimal(str(state["days_to_next_new_moon"])),
            "days_to_next_full_moon": Decimal(str(state["days_to_next_full_moon"])),
            "is_lunar_eclipse": state["is_lunar_eclipse"],
            "is_solar_eclipse": state["is_solar_eclipse"],
            "mercury_retrograde": state["mercury_retrograde"],
            "venus_retrograde": state["venus_retrograde"],
            "mars_retrograde": state["mars_retrograde"],
            "jupiter_retrograde": state["jupiter_retrograde"],
            "saturn_retrograde": state["saturn_retrograde"],
            "retrograde_count": state["retrograde_count"],
            "sun_longitude": Decimal(str(state["sun_longitude"])),
            "moon_longitude": Decimal(str(state["moon_longitude"])),
            "mercury_longitude": Decimal(str(state["mercury_longitude"])),
            "venus_longitude": Decimal(str(state["venus_longitude"])),
            "mars_longitude": Decimal(str(state["mars_longitude"])),
            "jupiter_longitude": Decimal(str(state["jupiter_longitude"])),
            "saturn_longitude": Decimal(str(state["saturn_longitude"])),
            "active_aspects": state["active_aspects"],
            "ingresses": state["ingresses"],
            "celestial_score": Decimal(str(state["celestial_score"])),
        }

        update_cols = {k: v for k, v in row.items() if k != "timestamp"}
        stmt = pg_insert(CelestialState).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp"],
            set_=update_cols,
        )
        db.execute(stmt)
        db.commit()
