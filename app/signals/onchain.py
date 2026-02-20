"""Layer 2: On-chain analytics signal engine.

Fetches exchange flows, whale activity, NUPL, MVRV Z-Score, and SOPR.
Outputs onchain_score in range -1.0 to +1.0.
"""


class OnchainAnalyzer:
    """Compute on-chain metrics and composite score."""

    def fetch_metrics(self, symbol: str) -> dict:
        """Fetch latest on-chain metrics from data source."""
        raise NotImplementedError

    def compute_score(self, metrics: dict) -> float:
        """Compute onchain_score from metrics."""
        raise NotImplementedError
