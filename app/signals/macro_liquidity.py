"""Layer 7: Macro Liquidity & Carry Trade signal engine.

Thin facade over macro_signal_service — follows the same pattern as
onchain.py, celestial.py, etc.

Outputs macro_score in range [-1.0, +1.0] plus regime classification.
"""

import logging

from sqlalchemy.orm import Session

from app.services.fred_fetch import is_available as fred_available
from app.services.macro_signal_service import compute_macro_signal

logger = logging.getLogger(__name__)


class MacroLiquidityAnalyzer:
    """Compute macro liquidity composite signal."""

    def is_available(self) -> bool:
        """Check if at least one macro data source is configured."""
        return fred_available()

    def compute_and_store(self, db: Session) -> dict | None:
        """Compute all sub-signals, composite score, and persist.

        Returns full signal dict or None if no data sources available.
        """
        if not self.is_available():
            logger.debug("No macro data sources configured — skipping")
            return None
        return compute_macro_signal(db)
