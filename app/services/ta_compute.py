"""Manual Technical Analysis indicator computation.

All indicators are computed using pandas + numpy only (no pandas-ta).
Functions operate on pandas DataFrames/Series with OHLCV columns.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Moving Averages
# ---------------------------------------------------------------------------

def compute_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period, min_periods=period).mean()


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


# ---------------------------------------------------------------------------
# RSI (Wilder's smoothed)
# ---------------------------------------------------------------------------

def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing method."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    # First average uses SMA, then Wilder's smoothing (EMA with alpha=1/period)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, and histogram.

    Returns:
        (macd_line, signal_line, histogram)
    """
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ---------------------------------------------------------------------------
# Stochastic Oscillator
# ---------------------------------------------------------------------------

def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """Stochastic %K and %D.

    Returns:
        (stoch_k, stoch_d)
    """
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()

    denom = highest_high - lowest_low
    stoch_k = 100 * (close - lowest_low) / denom.replace(0, np.nan)
    stoch_d = stoch_k.rolling(window=d_period, min_periods=d_period).mean()
    return stoch_k, stoch_d


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def compute_bollinger(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands (upper, middle, lower).

    Returns:
        (bb_upper, bb_middle, bb_lower)
    """
    bb_middle = compute_sma(close, period)
    rolling_std = close.rolling(window=period, min_periods=period).std()
    bb_upper = bb_middle + std_dev * rolling_std
    bb_lower = bb_middle - std_dev * rolling_std
    return bb_upper, bb_middle, bb_lower


# ---------------------------------------------------------------------------
# ATR (Average True Range)
# ---------------------------------------------------------------------------

def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range using Wilder's smoothing."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return atr


# ---------------------------------------------------------------------------
# Fibonacci Retracement
# ---------------------------------------------------------------------------

def compute_fibonacci(
    high: pd.Series,
    low: pd.Series,
    lookback: int = 50,
) -> dict[str, float]:
    """Fibonacci retracement levels from the lookback period high and low.

    Returns:
        Dict with keys: fib_0, fib_236, fib_382, fib_500, fib_618, fib_786, fib_1000
    """
    period_high = high.iloc[-lookback:].max()
    period_low = low.iloc[-lookback:].min()
    diff = period_high - period_low

    return {
        "fib_0": float(period_high),
        "fib_236": float(period_high - 0.236 * diff),
        "fib_382": float(period_high - 0.382 * diff),
        "fib_500": float(period_high - 0.500 * diff),
        "fib_618": float(period_high - 0.618 * diff),
        "fib_786": float(period_high - 0.786 * diff),
        "fib_1000": float(period_low),
    }


# ---------------------------------------------------------------------------
# Composite TA Score
# ---------------------------------------------------------------------------

def compute_ta_score(indicators: dict) -> float:
    """Compute weighted composite TA score normalized to [-1.0, +1.0].

    Weights:
        RSI:        0.20
        MACD:       0.20
        Stochastic: 0.15
        Bollinger:  0.15
        Trend:      0.20
        ATR:        0.10
    """
    score = 0.0

    # RSI component: (RSI - 50) / 50 → range [-1, +1]
    rsi = indicators.get("rsi_14")
    if rsi is not None and not np.isnan(rsi):
        score += 0.20 * (rsi - 50) / 50

    # MACD component: histogram sign with magnitude dampening
    macd_hist = indicators.get("macd_histogram")
    if macd_hist is not None and not np.isnan(macd_hist):
        # Normalize by clamping to [-1, +1] via tanh-like scaling
        score += 0.20 * max(-1.0, min(1.0, float(np.sign(macd_hist))))

    # Stochastic component: (K - 50) / 50
    stoch_k = indicators.get("stoch_k")
    if stoch_k is not None and not np.isnan(stoch_k):
        score += 0.15 * (stoch_k - 50) / 50

    # Bollinger component: position within bands → [-1, +1]
    close = indicators.get("close")
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    if all(v is not None and not np.isnan(v) for v in [close, bb_upper, bb_lower]):
        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            bb_pos = 2 * (close - bb_lower) / bb_range - 1  # [-1, +1]
            score += 0.15 * max(-1.0, min(1.0, bb_pos))

    # Trend component: price vs SMA alignment
    sma_20 = indicators.get("sma_20")
    sma_50 = indicators.get("sma_50")
    sma_200 = indicators.get("sma_200")
    if close is not None and not np.isnan(close):
        trend_signals = 0
        trend_count = 0
        for sma in [sma_20, sma_50, sma_200]:
            if sma is not None and not np.isnan(sma):
                trend_signals += 1 if close > sma else -1
                trend_count += 1
        if trend_count > 0:
            score += 0.20 * (trend_signals / trend_count)

    # ATR component: volatility awareness (high ATR → slight bearish bias)
    atr = indicators.get("atr_14")
    if atr is not None and close is not None:
        if not np.isnan(atr) and not np.isnan(close) and close > 0:
            atr_pct = atr / close
            # Normal ATR ~2-3% for crypto, high >5%
            atr_signal = -max(-1.0, min(1.0, (atr_pct - 0.03) / 0.03))
            score += 0.10 * atr_signal

    # Clamp final score to [-1.0, +1.0]
    return max(-1.0, min(1.0, round(score, 4)))


# ---------------------------------------------------------------------------
# Master Computation
# ---------------------------------------------------------------------------

def compute_all(df: pd.DataFrame) -> dict:
    """Compute all TA indicators from an OHLCV DataFrame.

    Expects columns: open, high, low, close, volume
    Requires at least 200 rows for SMA-200.

    Returns:
        Dict of all indicator values for the latest (last) row.
    """
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    # RSI
    rsi_14 = compute_rsi(close, 14)
    rsi_7 = compute_rsi(close, 7)

    # MACD
    macd_line, macd_signal, macd_histogram = compute_macd(close)

    # Stochastic
    stoch_k, stoch_d = compute_stochastic(high, low, close)

    # Moving averages
    sma_20 = compute_sma(close, 20)
    sma_50 = compute_sma(close, 50)
    sma_200 = compute_sma(close, 200)
    ema_12 = compute_ema(close, 12)
    ema_26 = compute_ema(close, 26)

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = compute_bollinger(close)

    # ATR
    atr_14 = compute_atr(high, low, close)

    # Fibonacci levels from last 50 candles
    fib = compute_fibonacci(high, low, lookback=50)

    # Assemble latest values
    idx = -1  # last row
    indicators = {
        "rsi_14": _val(rsi_14, idx),
        "rsi_7": _val(rsi_7, idx),
        "macd_line": _val(macd_line, idx),
        "macd_signal": _val(macd_signal, idx),
        "macd_histogram": _val(macd_histogram, idx),
        "stoch_k": _val(stoch_k, idx),
        "stoch_d": _val(stoch_d, idx),
        "sma_20": _val(sma_20, idx),
        "sma_50": _val(sma_50, idx),
        "sma_200": _val(sma_200, idx),
        "ema_12": _val(ema_12, idx),
        "ema_26": _val(ema_26, idx),
        "bb_upper": _val(bb_upper, idx),
        "bb_middle": _val(bb_middle, idx),
        "bb_lower": _val(bb_lower, idx),
        "atr_14": _val(atr_14, idx),
        "close": _val(close, idx),
        **fib,
    }

    # Composite score
    indicators["ta_score"] = compute_ta_score(indicators)

    return indicators


def _val(series: pd.Series, idx: int) -> float | None:
    """Extract a scalar value from a Series, returning None if NaN."""
    v = series.iloc[idx]
    if pd.isna(v):
        return None
    return float(v)
