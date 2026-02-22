"""Layer 5A: Political calendar engine.

Tracks scheduled political/economic events (FOMC, CPI, hearings, elections)
and computes proximity-based scores. Delegates to political_calendar_service.
"""

RECURRING_POLITICAL_EVENTS = [
    {"type": "fomc_meeting", "frequency": "8x/year", "volatility": "high", "category": "monetary_policy"},
    {"type": "cpi_release", "frequency": "monthly", "volatility": "high", "category": "monetary_policy"},
    {"type": "jobs_report", "frequency": "monthly", "volatility": "medium", "category": "fiscal_policy"},
    {"type": "gdp_release", "frequency": "quarterly", "volatility": "medium", "category": "fiscal_policy"},
    {"type": "sec_meeting", "frequency": "varies", "volatility": "high", "category": "crypto_regulation"},
    {"type": "treasury_refunding", "frequency": "quarterly", "volatility": "medium", "category": "monetary_policy"},
    {"type": "opec_meeting", "frequency": "~6x/year", "volatility": "medium", "category": "geopolitical"},
    {"type": "g7_g20_summit", "frequency": "annual", "volatility": "medium", "category": "geopolitical"},
    {"type": "us_election", "frequency": "2yr/4yr", "volatility": "extreme", "category": "election"},
    {"type": "debt_ceiling_deadline", "frequency": "irregular", "volatility": "extreme", "category": "fiscal_policy"},
]


class PoliticalCalendarEngine:
    """Track scheduled events and compute proximity-based scores."""

    def get_upcoming_events(self, db, days_ahead: int = 7) -> list:
        from app.services.political_calendar_service import get_upcoming_events
        return get_upcoming_events(db, days_ahead)

    def compute_calendar_score(self, db) -> dict:
        from app.services.political_calendar_service import compute_calendar_score
        return compute_calendar_score(db)
