"""Layer 4: Sentiment signal engine.

Fetches Fear & Greed Index, social sentiment, and Google Trends data.
Outputs sentiment_score in range -1.0 to +1.0.
"""


class SentimentAnalyzer:
    """Compute sentiment metrics and composite score."""

    def fetch_fear_greed(self) -> dict:
        """Fetch current Fear & Greed Index from Alternative.me."""
        raise NotImplementedError

    def compute_score(self, data: dict) -> float:
        """Compute sentiment_score from sentiment data."""
        raise NotImplementedError
