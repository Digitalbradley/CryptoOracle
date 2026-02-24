"""Shared utility functions used across routers and services."""


def normalize_symbol(symbol: str) -> str:
    """Normalize a trading pair symbol to CCXT format (e.g. BTC/USDT).

    Accepts:
        BTC-USDT, BTCUSDT, btc/usdt, BTC/USDT → BTC/USDT
        BTC, ETH, XRP → BTC/USDT, ETH/USDT, XRP/USDT

    This should be called at the router level before passing to any service.
    """
    s = symbol.upper().replace("-", "/")
    # If no separator found, try to insert one (e.g. BTCUSDT → BTC/USDT)
    if "/" not in s:
        for quote in ("USDT", "USDC", "BUSD", "USD", "BTC", "ETH"):
            if s.endswith(quote) and len(s) > len(quote):
                s = s[: -len(quote)] + "/" + quote
                break
        else:
            # Bare symbol (e.g. "BTC") → default to /USDT pair
            s = s + "/USDT"
    return s
