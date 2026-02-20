"""Backtesting modules for cycle validation and signal performance.

Includes the 47-day cycle backtester (priority #1) and general signal backtester.
"""


class CycleBacktester:
    """Validate N-day crash cycle hypotheses against historical data."""

    def run(
        self,
        cycle_days: int,
        tolerance: int = 2,
        min_drop_pct: float = 10.0,
    ) -> dict:
        raise NotImplementedError


class SignalBacktester:
    """Backtest any signal layer or combination against historical price data."""

    def run(
        self, layers: list, weights: dict, threshold: float = 0.5
    ) -> dict:
        raise NotImplementedError
