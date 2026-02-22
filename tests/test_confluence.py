"""Tests for the confluence score endpoints."""

from unittest.mock import patch, MagicMock

from tests.conftest import (
    make_confluence_row,
    make_signal_weights_row,
    setup_scalars_all,
)


def test_get_confluence(client, mock_db):
    """GET /api/confluence/{symbol} computes and returns scores."""
    mock_result = {
        "ta_score": 0.7,
        "onchain_score": 0.2,
        "celestial_score": 0.5,
        "numerology_score": 0.3,
        "sentiment_score": -0.2,
        "political_score": None,
        "composite_score": 0.35,
        "signal_strength": "buy",
        "aligned_layers": {"direction": "bullish", "layers": ["ta", "celestial"]},
        "alignment_count": 3,
        "weights": {"ta": 0.25, "onchain": 0.20},
    }

    with patch("app.routers.confluence.ConfluenceEngine") as MockEngine:
        MockEngine.return_value.compute_and_store.return_value = mock_result
        resp = client.get("/api/confluence/BTCUSDT?timeframe=1h")

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["timeframe"] == "1h"
    assert data["composite_score"] == 0.35
    assert data["signal_strength"] == "buy"
    assert data["alignment_count"] == 3
    assert data["scores"]["ta_score"] == 0.7
    assert data["scores"]["political_score"] is None


def test_get_confluence_history(client, mock_db):
    """GET /api/confluence/{symbol}/history returns historical scores."""
    rows = [make_confluence_row(), make_confluence_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/confluence/BTCUSDT/history?timeframe=1d&limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["count"] == 2
    assert data["data"][0]["signal_strength"] == "buy"


def test_get_confluence_history_empty(client, mock_db):
    """Returns empty list when no history."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/confluence/BTCUSDT/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_get_weights(client, mock_db):
    """GET /api/confluence/weights returns active weight profile."""
    with patch("app.routers.confluence.ConfluenceEngine") as MockEngine:
        MockEngine.return_value.get_active_weights.return_value = {
            "ta": 0.25,
            "onchain": 0.20,
            "celestial": 0.15,
            "numerology": 0.10,
            "sentiment": 0.15,
            "political": 0.15,
        }
        resp = client.get("/api/confluence/weights")

    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"] == "active"
    assert data["weights"]["ta"] == 0.25
    assert data["weights"]["sentiment"] == 0.15


def test_update_weights_valid(client, mock_db):
    """POST /api/confluence/weights updates weights that sum to 1.0."""
    setup_scalars_all(mock_db, [])  # no existing active profiles

    resp = client.post("/api/confluence/weights", json={
        "ta": 0.30,
        "onchain": 0.20,
        "celestial": 0.15,
        "numerology": 0.10,
        "sentiment": 0.15,
        "political": 0.10,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "updated"
    assert data["weights"]["ta"] == 0.30

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_update_weights_invalid_sum(client, mock_db):
    """POST /api/confluence/weights rejects weights that don't sum to 1.0."""
    resp = client.post("/api/confluence/weights", json={
        "ta": 0.50,
        "onchain": 0.50,
        "celestial": 0.15,
        "numerology": 0.10,
        "sentiment": 0.15,
        "political": 0.15,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert "sum to 1.0" in data["error"]

    mock_db.commit.assert_not_called()
