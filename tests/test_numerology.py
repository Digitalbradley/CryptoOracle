"""Tests for the numerology, gematria, and cycle endpoints."""

from unittest.mock import patch, MagicMock

from tests.conftest import (
    make_numerology_row,
    make_gematria_row,
    setup_scalar_one_or_none,
    setup_scalars_all,
)


def test_get_current_numerology_cached(client, mock_db):
    """GET /api/numerology/current returns cached row."""
    row = make_numerology_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/numerology/current")
    assert resp.status_code == 200
    data = resp.json()
    assert "date" in data
    assert data["numerology"]["universal_day_number"] == 6
    assert data["numerology"]["numerology_score"] == "0.5234"


def test_get_current_numerology_computes_on_miss(client, mock_db):
    """When not cached, computes on-the-fly."""
    setup_scalar_one_or_none(mock_db, None)

    with patch("app.routers.numerology.compute_daily_numerology") as mock_compute:
        from datetime import date
        mock_compute.return_value = {
            "date": date(2026, 2, 21),
            "universal_day_number": 4,
            "date_digit_sum": 13,
            "is_master_number": False,
        }
        resp = client.get("/api/numerology/current")

    assert resp.status_code == 200
    assert resp.json()["numerology"]["universal_day_number"] == 4


def test_get_numerology_by_date(client, mock_db):
    """GET /api/numerology/{date} returns for specific date."""
    row = make_numerology_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/numerology/2026-01-15")
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-01-15"


def test_calculate_gematria(client):
    """GET /api/gematria/calculate returns computed values."""
    resp = client.get("/api/gematria/calculate?text=bitcoin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["text"] == "bitcoin"
    assert "values" in data
    assert "english_ordinal" in data["values"]
    assert "full_reduction" in data["values"]


def test_get_stored_gematria_term(client, mock_db):
    """GET /api/gematria/{term} returns stored values when available."""
    row = make_gematria_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/gematria/bitcoin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["term"] == "bitcoin"
    assert data["stored"] is True
    assert data["digit_sum"] == 5
    assert data["associated_planet"] == "Mercury"


def test_get_gematria_term_not_stored(client, mock_db):
    """GET /api/gematria/{term} computes on-the-fly when not stored."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.get("/api/gematria/ethereum")
    assert resp.status_code == 200
    data = resp.json()
    assert data["term"] == "ethereum"
    assert data["stored"] is False
    assert "values" in data


def test_list_cycles(client, mock_db):
    """GET /api/cycles returns list of active cycles."""
    with patch("app.routers.numerology.cycle_tracker") as mock_ct:
        mock_ct.get_all_active.return_value = [
            {"name": "47-day", "cycle_days": 47, "hit_rate": 0.83}
        ]
        resp = client.get("/api/cycles")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["cycles"][0]["name"] == "47-day"


def test_check_cycles_for_date(client, mock_db):
    """GET /api/cycles/check/{date} returns alignment info."""
    with patch("app.routers.numerology.cycle_tracker") as mock_ct:
        mock_ct.check_date.return_value = [
            {"cycle_name": "47-day", "is_aligned": True, "days_offset": 0}
        ]
        resp = client.get("/api/cycles/check/2026-01-15")

    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-01-15"
    assert data["aligned_count"] == 1
