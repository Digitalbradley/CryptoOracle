"""Layer 5C: Narrative detector.

Identifies dominant political/macro narratives that persist over days/weeks
by clustering recent classified news articles.
Delegates to political_narrative_service.
"""


class NarrativeDetector:
    """Detect and track persistent political/macro narratives."""

    def detect_narratives(self, db, hours_lookback: int = 72) -> list:
        from app.services.political_narrative_service import detect_narratives
        return detect_narratives(db, hours_lookback)

    def get_dominant_narrative(self, db) -> dict | None:
        from app.services.political_narrative_service import get_dominant_narrative
        return get_dominant_narrative(db)
