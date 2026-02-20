"""Layer 3A: Celestial/Astronomical signal engine.

Uses pyswisseph to compute lunar phases, planetary retrogrades,
aspects, eclipses, and ingresses. Outputs celestial_score in range -1.0 to +1.0.
"""


class CelestialEngine:
    """Compute daily celestial state and score."""

    def compute_daily_state(self, date) -> dict:
        """Compute full celestial state for a given date."""
        raise NotImplementedError

    def compute_score(self, state: dict) -> float:
        """Compute celestial_score from celestial state."""
        raise NotImplementedError
