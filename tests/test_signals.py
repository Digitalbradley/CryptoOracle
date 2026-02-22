"""Tests for the TA signals endpoints."""

from tests.conftest import make_ta_row, setup_scalar_one_or_none, setup_scalars_all


def test_get_ta_indicators(client, mock_db):
    """GET /api/signals/ta/{symbol} returns latest TA row."""
    row = make_ta_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/signals/ta/BTC-USDT?timeframe=1h")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["timeframe"] == "1h"
    assert data["indicators"] is not None
    assert data["indicators"]["rsi_14"] == "65.2345"
    assert data["indicators"]["ta_score"] == "0.7234"


def test_get_ta_indicators_none(client, mock_db):
    """Returns null indicators when no TA data exists."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.get("/api/signals/ta/BTC-USDT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["indicators"] is None


def test_get_ta_history(client, mock_db):
    """GET /api/signals/ta/{symbol}/history returns list."""
    rows = [make_ta_row(), make_ta_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/signals/ta/BTC-USDT/history?timeframe=1d&limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["count"] == 2
    assert len(data["data"]) == 2


def test_get_ta_history_empty(client, mock_db):
    """Returns empty list when no history available."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/signals/ta/BTC-USDT/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
