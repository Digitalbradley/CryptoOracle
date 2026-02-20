"""Test the health check endpoint."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Health endpoint should return 200 with status info."""
    # Mock the database dependency to avoid requiring a real DB for tests
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1

    mock_db = MagicMock()
    mock_db.execute.return_value = mock_result

    def override_get_db():
        yield mock_db

    from app.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["version"] == "0.1.0"

    # Clean up override
    app.dependency_overrides.clear()
