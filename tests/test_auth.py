"""Tests for authentication endpoints and middleware."""

from unittest.mock import MagicMock, patch

from tests.conftest import setup_scalar_one_or_none


def test_login_success(anon_client, mock_db):
    """POST /api/auth/login with valid credentials returns 200 and sets cookie."""
    from app.services.auth_service import hash_password

    user = MagicMock()
    user.username = "admin"
    user.hashed_password = hash_password("secret123")
    user.last_login = None
    setup_scalar_one_or_none(mock_db, user)

    resp = anon_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "secret123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authenticated"
    assert data["username"] == "admin"
    assert "access_token" in resp.cookies


def test_login_invalid_credentials(anon_client, mock_db):
    """POST /api/auth/login with bad credentials returns 401."""
    setup_scalar_one_or_none(mock_db, None)

    resp = anon_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


def test_logout_clears_cookie(client):
    """POST /api/auth/logout clears the access_token cookie."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["status"] == "logged_out"


def test_me_authenticated(client):
    """GET /api/auth/me with valid cookie returns username."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "testadmin"


def test_me_unauthenticated(anon_client):
    """GET /api/auth/me without cookie returns 401."""
    resp = anon_client.get("/api/auth/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_protected_endpoint_without_auth(anon_client, mock_db):
    """Protected endpoint returns 401 without auth cookie."""
    resp = anon_client.get("/api/price/BTC-USDT")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


def test_health_always_public(anon_client, mock_db):
    """Health endpoint works without auth."""
    mock_db.execute.return_value.scalar.return_value = 1
    resp = anon_client.get("/health")
    assert resp.status_code == 200


def test_expired_token_returns_401(anon_client):
    """Expired JWT token returns 401."""
    from datetime import datetime, timedelta, timezone

    from jose import jwt

    from app.config import settings

    expired_payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=25),
    }
    expired_token = jwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    anon_client.cookies.set("access_token", expired_token)
    resp = anon_client.get("/api/price/BTC-USDT")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired token"
