"""Layer 4: Sentiment signal engine.

Fetches Fear & Greed Index from Alternative.me and computes
contrarian sentiment_score in range [-1.0, +1.0].
"""

import logging

from sqlalchemy.orm import Session

from app.services.sentiment_fetch import (
    compute_sentiment_score,
    fetch_and_store_current,
    fetch_fear_greed_current,
)

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Compute sentiment metrics and composite score."""

    def fetch_fear_greed(self) -> dict | None:
        """Fetch current Fear & Greed Index from Alternative.me."""
        return fetch_fear_greed_current()

    def compute_score(self, data: dict) -> float:
        """Compute sentiment_score from Fear & Greed data.

        Args:
            data: {"value": int, "label": str, "timestamp": datetime}

        Returns:
            Score in range [-1.0, +1.0]
        """
        return compute_sentiment_score(data["value"])

    def fetch_and_store(self, db: Session, symbols: list[str]) -> int:
        """Fetch current sentiment and store for all watched symbols.

        Returns:
            Number of rows upserted
        """
        return fetch_and_store_current(db, symbols)
