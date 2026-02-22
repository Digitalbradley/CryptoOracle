"""Tests for the backtester endpoints."""

from unittest.mock import patch


def test_run_cycle_backtest(client, mock_db):
    """POST /api/backtest/cycle runs and returns report."""
    mock_report = {
        "total_crash_events": 15,
        "cycle_analysis": {
            "is_significant": True,
            "p_value": 0.003,
            "conclusion": "47-day cycle is statistically significant",
        },
    }

    with patch("app.routers.backtest.CycleBacktester") as MockBT:
        MockBT.return_value.generate_report.return_value = mock_report
        resp = client.post("/api/backtest/cycle", json={
            "symbol": "BTC/USDT",
            "min_magnitude": -10.0,
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["report"]["total_crash_events"] == 15
    assert data["report"]["cycle_analysis"]["is_significant"] is True


def test_run_cycle_backtest_defaults(client, mock_db):
    """POST /api/backtest/cycle works with default body values."""
    mock_report = {"total_crash_events": 5, "cycle_analysis": {"is_significant": False}}

    with patch("app.routers.backtest.CycleBacktester") as MockBT:
        MockBT.return_value.generate_report.return_value = mock_report
        resp = client.post("/api/backtest/cycle", json={})

    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"


def test_run_signal_backtest(client, mock_db):
    """POST /api/backtest/signals runs replay and returns accuracy."""
    mock_predictions = [{"date": "2026-01-01", "signal": "buy"}] * 100

    with patch("app.routers.backtest.SignalBacktester") as MockBT:
        instance = MockBT.return_value
        instance.replay_historical.return_value = mock_predictions
        instance.compute_accuracy.return_value = 0.72

        resp = client.post("/api/backtest/signals", json={
            "symbol": "BTC/USDT",
            "timeframe": "1d",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["total_days_replayed"] == 100
    assert data["accuracy"] == 0.72


def test_run_weight_optimizer(client, mock_db):
    """POST /api/backtest/optimize returns best weights."""
    mock_result = {
        "best_weights": {"ta": 0.30, "onchain": 0.25},
        "best_7day_hit_rate": 0.78,
        "iterations": 252,
    }

    with patch("app.routers.backtest.SignalBacktester") as MockBT:
        MockBT.return_value.optimize_weights.return_value = mock_result

        resp = client.post("/api/backtest/optimize", json={
            "symbol": "BTC/USDT",
            "timeframe": "1d",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert data["best_7day_hit_rate"] == 0.78
