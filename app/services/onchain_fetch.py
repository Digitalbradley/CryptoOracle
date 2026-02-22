"""On-chain data fetcher — CryptoQuant + Glassnode dual-provider.

CryptoQuant: Exchange flows, whale activity (short-term trading signals).
Glassnode: NUPL, MVRV Z-Score, SOPR, active addresses (macro cycle metrics).

Both providers are gated behind API key checks. If no keys are configured,
all functions return None and the confluence engine skips this layer.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.onchain_metrics import OnchainMetrics

logger = logging.getLogger(__name__)

# API base URLs
CRYPTOQUANT_BASE = "https://api.cryptoquant.com/v1"
GLASSNODE_BASE = "https://api.glassnode.com/v1/metrics"

# Symbol mapping: CCXT format → provider format
_SYMBOL_MAP_CQ = {
    "BTC/USDT": "btc",
    "ETH/USDT": "eth",
}
_SYMBOL_MAP_GL = {
    "BTC/USDT": "BTC",
    "ETH/USDT": "ETH",
}


def is_available() -> bool:
    """Check if at least one on-chain API key is configured."""
    return bool(settings.cryptoquant_api_key or settings.glassnode_api_key)


def _has_cryptoquant() -> bool:
    return bool(settings.cryptoquant_api_key)


def _has_glassnode() -> bool:
    return bool(settings.glassnode_api_key)


# ---- CryptoQuant fetchers ----


def fetch_exchange_flows(symbol: str) -> dict | None:
    """Fetch exchange inflow/outflow/netflow from CryptoQuant.

    Returns:
        {"exchange_inflow": float, "exchange_outflow": float, "exchange_netflow": float}
        or None if unavailable
    """
    if not _has_cryptoquant():
        return None

    asset = _SYMBOL_MAP_CQ.get(symbol)
    if not asset:
        return None

    try:
        headers = {"Authorization": f"Bearer {settings.cryptoquant_api_key}"}
        resp = httpx.get(
            f"{CRYPTOQUANT_BASE}/{asset}/exchange-flows/exchange-netflow-total",
            headers=headers,
            params={"window": "day", "limit": 1},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if "result" not in data or "data" not in data["result"]:
            return None

        latest = data["result"]["data"][-1] if data["result"]["data"] else None
        if not latest:
            return None

        return {
            "exchange_inflow": float(latest.get("in_total", 0)),
            "exchange_outflow": float(latest.get("out_total", 0)),
            "exchange_netflow": float(latest.get("netflow_total", 0)),
        }
    except Exception:
        logger.exception("CryptoQuant exchange flows fetch failed for %s", symbol)
        return None


def fetch_whale_activity(symbol: str) -> dict | None:
    """Fetch whale transaction data from CryptoQuant.

    Returns:
        {"whale_transactions_count": int, "whale_volume_usd": float}
        or None if unavailable
    """
    if not _has_cryptoquant():
        return None

    asset = _SYMBOL_MAP_CQ.get(symbol)
    if not asset:
        return None

    try:
        headers = {"Authorization": f"Bearer {settings.cryptoquant_api_key}"}
        resp = httpx.get(
            f"{CRYPTOQUANT_BASE}/{asset}/network-data/transactions-count-large",
            headers=headers,
            params={"window": "day", "limit": 1},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if "result" not in data or "data" not in data["result"]:
            return None

        latest = data["result"]["data"][-1] if data["result"]["data"] else None
        if not latest:
            return None

        return {
            "whale_transactions_count": int(latest.get("transactions_count_large", 0)),
            "whale_volume_usd": float(latest.get("transactions_volume_large_usd", 0)),
        }
    except Exception:
        logger.exception("CryptoQuant whale activity fetch failed for %s", symbol)
        return None


# ---- Glassnode fetchers ----


def _glassnode_get(endpoint: str, asset: str) -> float | None:
    """Generic Glassnode API getter for a single-value metric."""
    try:
        resp = httpx.get(
            f"{GLASSNODE_BASE}/{endpoint}",
            params={
                "a": asset,
                "api_key": settings.glassnode_api_key,
                "i": "24h",  # daily resolution
                "s": None,   # latest
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return None

        # Glassnode returns list of {t: timestamp, v: value}
        latest = data[-1] if isinstance(data, list) else None
        if latest and "v" in latest:
            return float(latest["v"])
        return None
    except Exception:
        logger.exception("Glassnode fetch failed for %s/%s", endpoint, asset)
        return None


def fetch_nupl(symbol: str) -> float | None:
    """Fetch Net Unrealized Profit/Loss from Glassnode."""
    if not _has_glassnode():
        return None
    asset = _SYMBOL_MAP_GL.get(symbol)
    if not asset:
        return None
    return _glassnode_get("market/net_unrealized_profit_loss", asset)


def fetch_mvrv_zscore(symbol: str) -> float | None:
    """Fetch MVRV Z-Score from Glassnode."""
    if not _has_glassnode():
        return None
    asset = _SYMBOL_MAP_GL.get(symbol)
    if not asset:
        return None
    return _glassnode_get("market/mvrv_z_score", asset)


def fetch_sopr(symbol: str) -> float | None:
    """Fetch Spent Output Profit Ratio from Glassnode."""
    if not _has_glassnode():
        return None
    asset = _SYMBOL_MAP_GL.get(symbol)
    if not asset:
        return None
    return _glassnode_get("indicators/sopr", asset)


def fetch_active_addresses(symbol: str) -> int | None:
    """Fetch active address count from Glassnode."""
    if not _has_glassnode():
        return None
    asset = _SYMBOL_MAP_GL.get(symbol)
    if not asset:
        return None
    val = _glassnode_get("addresses/active_count", asset)
    return int(val) if val is not None else None


# ---- Score computation ----


def compute_onchain_score(metrics: dict) -> float:
    """Compute weighted on-chain composite score from available metrics.

    Each metric maps to a sub-score in [-1.0, +1.0]. Only non-None metrics
    contribute. The final score is the weighted average of available sub-scores.

    Returns:
        Score in range [-1.0, +1.0], or 0.0 if no metrics available
    """
    sub_scores = []
    sub_weights = []

    # Exchange netflow: negative = bullish (coins leaving exchanges)
    netflow = metrics.get("exchange_netflow")
    if netflow is not None:
        if netflow < -1000:
            sub_scores.append(0.5)
        elif netflow < 0:
            sub_scores.append(0.3)
        elif netflow < 1000:
            sub_scores.append(-0.1)
        else:
            sub_scores.append(-0.3)
        sub_weights.append(0.20)

    # NUPL: > 0.75 euphoria (bearish), < 0 capitulation (bullish)
    nupl = metrics.get("nupl")
    if nupl is not None:
        if nupl > 0.75:
            sub_scores.append(-0.5)
        elif nupl > 0.5:
            sub_scores.append(-0.3)
        elif nupl > 0.25:
            sub_scores.append(0.0)
        elif nupl > 0:
            sub_scores.append(0.2)
        else:
            sub_scores.append(0.5)  # Capitulation → bullish
        sub_weights.append(0.25)

    # MVRV Z-Score: > 7 overvalued (bearish), < 0 undervalued (bullish)
    mvrv = metrics.get("mvrv_zscore")
    if mvrv is not None:
        if mvrv > 7:
            sub_scores.append(-0.5)
        elif mvrv > 3:
            sub_scores.append(-0.3)
        elif mvrv > 1:
            sub_scores.append(0.0)
        elif mvrv > 0:
            sub_scores.append(0.2)
        else:
            sub_scores.append(0.4)  # Undervalued → bullish
        sub_weights.append(0.25)

    # SOPR: < 1 selling at loss (contrarian bullish), > 1.05 taking profit
    sopr = metrics.get("sopr")
    if sopr is not None:
        if sopr < 0.95:
            sub_scores.append(0.4)  # Deep loss selling → bullish
        elif sopr < 1.0:
            sub_scores.append(0.3)
        elif sopr < 1.02:
            sub_scores.append(0.0)
        elif sopr < 1.05:
            sub_scores.append(-0.1)
        else:
            sub_scores.append(-0.2)
        sub_weights.append(0.20)

    # Whale activity: high count → uncertainty
    whale_count = metrics.get("whale_transactions_count")
    if whale_count is not None:
        # This is neutral by default — very high whale activity signals volatility
        if whale_count > 500:
            sub_scores.append(-0.1)  # Slight bearish (distribution risk)
        else:
            sub_scores.append(0.0)
        sub_weights.append(0.10)

    if not sub_scores:
        return 0.0

    # Weighted average
    total_weight = sum(sub_weights)
    score = sum(s * w for s, w in zip(sub_scores, sub_weights)) / total_weight

    return round(max(-1.0, min(1.0, score)), 4)


# ---- Fetch + Store ----


def fetch_all_metrics(symbol: str) -> dict:
    """Fetch all available on-chain metrics for a symbol.

    Returns dict with available metrics (None values for unavailable).
    """
    metrics = {}

    # CryptoQuant: exchange flows
    flows = fetch_exchange_flows(symbol)
    if flows:
        metrics.update(flows)

    # CryptoQuant: whale activity
    whales = fetch_whale_activity(symbol)
    if whales:
        metrics.update(whales)

    # Glassnode: macro metrics
    metrics["nupl"] = fetch_nupl(symbol)
    metrics["mvrv_zscore"] = fetch_mvrv_zscore(symbol)
    metrics["sopr"] = fetch_sopr(symbol)
    metrics["active_addresses"] = fetch_active_addresses(symbol)

    return metrics


def upsert_onchain(db: Session, metrics: dict, symbol: str, timestamp: datetime) -> None:
    """Persist on-chain metrics to onchain_metrics table."""
    score = compute_onchain_score(metrics)

    row = {
        "timestamp": timestamp,
        "symbol": symbol,
        "exchange_inflow": _to_decimal(metrics.get("exchange_inflow")),
        "exchange_outflow": _to_decimal(metrics.get("exchange_outflow")),
        "exchange_netflow": _to_decimal(metrics.get("exchange_netflow")),
        "whale_transactions_count": metrics.get("whale_transactions_count"),
        "whale_volume_usd": _to_decimal(metrics.get("whale_volume_usd")),
        "active_addresses": metrics.get("active_addresses"),
        "nupl": _to_decimal(metrics.get("nupl")),
        "mvrv_zscore": _to_decimal(metrics.get("mvrv_zscore")),
        "sopr": _to_decimal(metrics.get("sopr")),
        "onchain_score": Decimal(str(score)),
    }

    # Remove None values so they don't overwrite existing data
    row = {k: v for k, v in row.items() if v is not None}
    # But always include the keys needed for the upsert
    row.setdefault("timestamp", timestamp)
    row.setdefault("symbol", symbol)

    stmt = pg_insert(OnchainMetrics).values([row])
    update_cols = {
        k: getattr(stmt.excluded, k)
        for k in row
        if k not in ("timestamp", "symbol")
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=["timestamp", "symbol"],
        set_=update_cols,
    )
    db.execute(stmt)
    db.commit()


def fetch_and_store(db: Session, symbol: str) -> dict | None:
    """Fetch all available on-chain metrics and store.

    Returns:
        Metrics dict if any data was fetched, None if no providers available
    """
    if not is_available():
        logger.debug("No on-chain API keys configured — skipping")
        return None

    metrics = fetch_all_metrics(symbol)

    # Check if we got any actual data
    has_data = any(
        v is not None
        for k, v in metrics.items()
        if k not in ("timestamp", "symbol")
    )
    if not has_data:
        logger.warning("On-chain fetch returned no data for %s", symbol)
        return None

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    upsert_onchain(db, metrics, symbol, now)

    score = compute_onchain_score(metrics)
    logger.info("On-chain stored for %s: score=%.4f", symbol, score)
    return metrics


def _to_decimal(val) -> Decimal | None:
    """Convert a numeric value to Decimal, or return None."""
    if val is None:
        return None
    return Decimal(str(val))
