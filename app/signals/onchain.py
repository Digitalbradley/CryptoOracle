"""Layer 2: On-chain analytics signal engine.

Dual-provider: CryptoQuant (exchange flows, whales) + Glassnode (NUPL, MVRV, SOPR).
Gated behind API key checks — returns None if no keys configured.
Outputs onchain_score in range [-1.0, +1.0].
"""

import logging

from sqlalchemy.orm import Session

from app.services.onchain_fetch import (
    compute_onchain_score,
    fetch_all_metrics,
    fetch_and_store,
    is_available,
)

logger = logging.getLogger(__name__)


class OnchainAnalyzer:
    """Compute on-chain metrics and composite score."""

    def is_available(self) -> bool:
        """Check if at least one on-chain API key is configured."""
        return is_available()

    def fetch_metrics(self, symbol: str) -> dict | None:
        """Fetch latest on-chain metrics from available providers.

        Returns:
            Dict of metrics, or None if no providers available.
        """
        if not self.is_available():
            return None
        return fetch_all_metrics(symbol)

    def compute_score(self, metrics: dict) -> float:
        """Compute onchain_score from metrics.

        Args:
            metrics: Dict of on-chain metric values

        Returns:
            Score in range [-1.0, +1.0]
        """
        return compute_onchain_score(metrics)

    def fetch_and_store(self, db: Session, symbol: str) -> dict | None:
        """Fetch all available metrics, compute score, and persist.

        Returns:
            Metrics dict if data fetched, None if no providers available.
        """
        return fetch_and_store(db, symbol)
