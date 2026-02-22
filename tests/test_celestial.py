"""Tests for the celestial state endpoints."""

from unittest.mock import patch

from tests.conftest import make_celestial_row, setup_scalar_one_or_none, setup_scalars_all


def test_get_current_celestial_cached(client, mock_db):
    """GET /api/celestial/current returns cached state from DB."""
    row = make_celestial_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/celestial/current")
    assert resp.status_code == 200
    data = resp.json()
    assert "date" in data
    assert data["state"] is not None
    assert data["state"]["lunar_phase_name"] == "Waxing Gibbous"
    assert data["state"]["mercury_retrograde"] is False


def test_get_current_celestial_computes_on_miss(client, mock_db):
    """When no cached state, computes on-the-fly via CelestialEngine."""
    setup_scalar_one_or_none(mock_db, None)

    with patch("app.routers.celestial.CelestialEngine") as MockEngine:
        engine_instance = MockEngine.return_value
        engine_instance.compute_daily_state.return_value = {
            "lunar_phase_name": "New Moon",
            "mercury_retrograde": True,
        }
        resp = client.get("/api/celestial/current")

    assert resp.status_code == 200
    data = resp.json()
    assert data["state"]["lunar_phase_name"] == "New Moon"


def test_get_celestial_by_date(client, mock_db):
    """GET /api/celestial/{date} returns state for specific date."""
    row = make_celestial_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/celestial/2026-01-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-01-15"


def test_get_celestial_history(client, mock_db):
    """GET /api/celestial/history returns list of states."""
    rows = [make_celestial_row(), make_celestial_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/celestial/history?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["data"]) == 2


def test_get_celestial_history_empty(client, mock_db):
    """Returns empty list when no history data exists."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/celestial/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
