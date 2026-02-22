"""Tests for the sentiment data endpoints."""

from tests.conftest import make_sentiment_row, setup_scalar_one_or_none, setup_scalars_all


def test_get_latest_sentiment(client, mock_db):
    """GET /api/sentiment/{symbol} returns latest sentiment."""
    row = make_sentiment_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/sentiment/BTCUSDT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["sentiment"]["fear_greed_index"] == 68
    assert data["sentiment"]["fear_greed_label"] == "Greed"
    assert data["sentiment"]["sentiment_score"] == "-0.3100"


def test_get_latest_sentiment_none(client, mock_db):
    """Returns null when no sentiment data available."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.get("/api/sentiment/BTCUSDT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sentiment"] is None
    assert "message" in data


def test_get_sentiment_history(client, mock_db):
    """GET /api/sentiment/{symbol}/history returns list."""
    rows = [make_sentiment_row(), make_sentiment_row(fear_greed_index=25)]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/sentiment/BTCUSDT/history?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["count"] == 2
    assert len(data["data"]) == 2


def test_get_sentiment_history_empty(client, mock_db):
    """Returns empty list when no history."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/sentiment/BTCUSDT/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
