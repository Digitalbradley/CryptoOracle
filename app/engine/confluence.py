"""Confluence scoring engine.

Gathers scores from all signal layers, applies configurable weights,
computes composite score, and detects layer alignment.
"""


class ConfluenceEngine:
    """Compute weighted composite confluence score."""

    def compute_score(
        self, symbol: str, timestamp=None, weights: dict | None = None
    ) -> dict:
        raise NotImplementedError

    def get_alignment(self, scores: dict) -> dict:
        raise NotImplementedError
