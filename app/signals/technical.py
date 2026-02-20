"""Layer 1: Traditional Technical Analysis signal engine.

Computes RSI, MACD, Stochastic, Bollinger Bands, SMA, EMA, ATR,
Fibonacci retracements, and volume profile from OHLCV data.
Outputs ta_score in range -1.0 to +1.0.
"""


class TechnicalAnalyzer:
    """Compute TA indicators and composite score from price data."""

    def compute_indicators(self, symbol: str, timeframe: str) -> dict:
        """Compute all TA indicators for the latest candle."""
        raise NotImplementedError

    def compute_score(self, indicators: dict) -> float:
        """Compute composite ta_score from indicator values."""
        raise NotImplementedError
