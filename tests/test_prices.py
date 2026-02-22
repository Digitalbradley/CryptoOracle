"""Tests for the price data endpoints."""

from tests.conftest import make_price_row, setup_scalars_all


def test_get_prices_returns_candles(client, mock_db):
    """GET /api/prices/{symbol} returns formatted candle data."""
    rows = [make_price_row(), make_price_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/prices/BTC-USDT?timeframe=1h&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["timeframe"] == "1h"
    assert data["count"] == 2
    assert len(data["data"]) == 2
    candle = data["data"][0]
    assert "timestamp" in candle
    assert "open" in candle
    assert "close" in candle
    assert "volume" in candle


def test_get_prices_symbol_normalization(client, mock_db):
    """Symbol with dashes is normalized to slashes and uppercased."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/prices/eth-usdt")
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "ETH/USDT"


def test_get_prices_empty(client, mock_db):
    """Returns empty candles list when no data exists."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/prices/BTC-USDT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["data"] == []


def test_get_price_history(client, mock_db):
    """GET /api/prices/{symbol}/history returns filtered data."""
    rows = [make_price_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/prices/BTC-USDT/history?timeframe=1d")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["timeframe"] == "1d"
    assert data["count"] == 1


def test_get_price_history_with_date_range(client, mock_db):
    """History endpoint accepts start and end query params."""
    setup_scalars_all(mock_db, [])

    resp = client.get(
        "/api/prices/BTC-USDT/history?start=2025-01-01T00:00:00&end=2025-12-31T23:59:59"
    )
    assert resp.status_code == 200
