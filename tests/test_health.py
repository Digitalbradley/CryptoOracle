"""Tests for the health check endpoint."""

from tests.conftest import setup_scalar_one_or_none
from unittest.mock import MagicMock


def test_health_ok(client, mock_db):
    """Health endpoint returns 200 with connected database."""
    result = MagicMock()
    result.scalar.return_value = 1
    mock_db.execute.return_value = result

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["version"] == "0.1.0"
    assert "build" in data


def test_health_db_error(client, mock_db):
    """Health endpoint returns degraded when DB is unreachable."""
    mock_db.execute.side_effect = Exception("connection refused")

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert "error" in data["database"]
