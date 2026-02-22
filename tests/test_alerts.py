"""Tests for the alerts management endpoints."""

from tests.conftest import make_alert_row, setup_scalar_one_or_none, setup_scalars_all


def test_list_alerts(client, mock_db):
    """GET /api/alerts returns list of alerts."""
    rows = [make_alert_row(), make_alert_row(id=2, alert_type="alignment")]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["alerts"]) == 2
    alert = data["alerts"][0]
    assert alert["symbol"] == "BTC/USDT"
    assert alert["status"] == "active"
    assert alert["severity"] == "warning"


def test_list_alerts_empty(client, mock_db):
    """Returns empty list when no alerts."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_get_alert_by_id(client, mock_db):
    """GET /api/alerts/{id} returns single alert."""
    row = make_alert_row(id=42)
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/alerts/42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 42
    assert data["alert_type"] == "confluence"


def test_get_alert_not_found(client, mock_db):
    """GET /api/alerts/{id} returns error for missing alert."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.get("/api/alerts/999")
    assert resp.status_code == 200
    assert resp.json()["error"] == "Alert not found"


def test_acknowledge_alert(client, mock_db):
    """POST /api/alerts/{id}/acknowledge updates status."""
    row = make_alert_row(id=5)
    setup_scalar_one_or_none(mock_db, row)

    resp = client.post("/api/alerts/5/acknowledge")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "acknowledged"
    assert data["alert_id"] == 5
    assert row.status == "acknowledged"
    assert row.acknowledged_at is not None
    mock_db.commit.assert_called_once()


def test_acknowledge_alert_not_found(client, mock_db):
    """POST /api/alerts/{id}/acknowledge returns error for missing alert."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.post("/api/alerts/999/acknowledge")
    assert resp.status_code == 200
    assert resp.json()["error"] == "Alert not found"


def test_dismiss_alert(client, mock_db):
    """POST /api/alerts/{id}/dismiss updates status."""
    row = make_alert_row(id=7)
    setup_scalar_one_or_none(mock_db, row)

    resp = client.post("/api/alerts/7/dismiss")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "dismissed"
    assert data["alert_id"] == 7
    assert row.status == "dismissed"
    mock_db.commit.assert_called_once()


def test_dismiss_alert_not_found(client, mock_db):
    """POST /api/alerts/{id}/dismiss returns error for missing alert."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.post("/api/alerts/999/dismiss")
    assert resp.status_code == 200
    assert resp.json()["error"] == "Alert not found"
