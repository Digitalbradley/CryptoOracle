"""Tests for the on-chain metrics endpoints."""

from unittest.mock import patch

from tests.conftest import make_onchain_row, setup_scalar_one_or_none, setup_scalars_all


def test_get_onchain_status(client):
    """GET /api/onchain/status returns provider configuration."""
    with patch("app.routers.onchain.settings") as mock_settings:
        mock_settings.cryptoquant_api_key = ""
        mock_settings.glassnode_api_key = ""

        resp = client.get("/api/onchain/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["cryptoquant"]["configured"] is False
    assert data["glassnode"]["configured"] is False
    assert data["any_available"] is False


def test_get_onchain_status_with_keys(client):
    """Status shows configured=True when API keys are set."""
    with patch("app.routers.onchain.settings") as mock_settings:
        mock_settings.cryptoquant_api_key = "test-key-123"
        mock_settings.glassnode_api_key = "test-key-456"

        resp = client.get("/api/onchain/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["cryptoquant"]["configured"] is True
    assert data["glassnode"]["configured"] is True
    assert data["any_available"] is True


def test_get_latest_onchain(client, mock_db):
    """GET /api/onchain/{symbol} returns latest metrics."""
    row = make_onchain_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/onchain/BTCUSDT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC/USDT"
    assert data["metrics"]["exchange_netflow"] == "-1111.11"
    assert data["metrics"]["whale_transactions_count"] == 45
    assert data["metrics"]["onchain_score"] == "0.2345"


def test_get_latest_onchain_none_no_keys(client, mock_db):
    """Returns helpful message when no data and no API keys."""
    setup_scalar_one_or_none(mock_db, None)

    with patch("app.routers.onchain.settings") as mock_settings:
        mock_settings.cryptoquant_api_key = ""
        mock_settings.glassnode_api_key = ""
        resp = client.get("/api/onchain/BTCUSDT")

    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"] is None
    assert "API keys" in data["message"]


def test_get_onchain_history(client, mock_db):
    """GET /api/onchain/{symbol}/history returns list."""
    rows = [make_onchain_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/onchain/BTCUSDT/history?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["data"][0]["exchange_netflow"] == "-1111.11"


def test_get_onchain_history_empty(client, mock_db):
    """Returns empty list when no history."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/onchain/BTCUSDT/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
