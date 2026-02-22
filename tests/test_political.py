"""Tests for the political events endpoints."""

from unittest.mock import patch

from tests.conftest import (
    make_political_calendar_row,
    make_political_news_row,
    make_political_signal_row,
    setup_scalar_one_or_none,
    setup_scalars_all,
)


def test_get_political_status(client):
    """GET /api/political/status returns source configuration."""
    with patch("app.routers.political.settings") as mock_settings:
        mock_settings.newsapi_key = ""
        mock_settings.gnews_api_key = ""
        mock_settings.anthropic_api_key = ""

        resp = client.get("/api/political/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["rss"]["configured"] is True
    assert data["newsapi"]["configured"] is False
    assert data["gnews"]["configured"] is False
    assert data["claude_classification"]["configured"] is False
    assert data["any_api_source"] is False


def test_get_political_status_with_keys(client):
    """Status shows configured=True when API keys are set."""
    with patch("app.routers.political.settings") as mock_settings:
        mock_settings.newsapi_key = "test-key-123"
        mock_settings.gnews_api_key = "test-key-456"
        mock_settings.anthropic_api_key = "test-key-789"

        resp = client.get("/api/political/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["newsapi"]["configured"] is True
    assert data["gnews"]["configured"] is True
    assert data["claude_classification"]["configured"] is True
    assert data["any_api_source"] is True


def test_get_calendar_events(client, mock_db):
    """GET /api/political/calendar returns upcoming events."""
    with patch("app.services.political_calendar_service.get_upcoming_events") as mock_fn:
        mock_fn.return_value = [
            {
                "id": 1,
                "event_date": "2026-03-18",
                "event_type": "fomc_meeting",
                "category": "monetary_policy",
                "title": "FOMC Meeting (Mar 17-18, 2026)",
                "description": "Federal Open Market Committee interest rate decision.",
                "country": "US",
                "expected_volatility": "high",
                "expected_direction": None,
                "crypto_relevance": 8,
                "date_gematria_value": 20,
                "event_title_gematria": None,
            }
        ]
        resp = client.get("/api/political/calendar?days_ahead=7")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["data"][0]["event_type"] == "fomc_meeting"
    assert data["data"][0]["category"] == "monetary_policy"


def test_get_calendar_events_empty(client, mock_db):
    """Returns empty list when no upcoming events."""
    with patch("app.services.political_calendar_service.get_upcoming_events") as mock_fn:
        mock_fn.return_value = []
        resp = client.get("/api/political/calendar")

    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_get_calendar_event_by_id(client, mock_db):
    """GET /api/political/calendar/{id} returns single event."""
    row = make_political_calendar_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/political/calendar/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["event"]["event_type"] == "fomc_meeting"
    assert data["event"]["title"] == "FOMC Meeting (Mar 17-18, 2026)"


def test_get_calendar_event_not_found(client, mock_db):
    """Returns null when event not found."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.get("/api/political/calendar/999")
    assert resp.status_code == 200
    assert resp.json()["event"] is None


def test_get_political_news(client, mock_db):
    """GET /api/political/news returns recent articles."""
    rows = [make_political_news_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/political/news?hours=24&limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["data"][0]["source_name"] == "CoinDesk"
    assert data["data"][0]["category"] == "crypto_regulation"
    assert data["data"][0]["crypto_relevance_score"] == "0.8500"


def test_get_political_news_empty(client, mock_db):
    """Returns empty list when no news."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/political/news")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_get_news_history(client, mock_db):
    """GET /api/political/news/history returns history."""
    rows = [make_political_news_row(), make_political_news_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/political/news/history?limit=100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2


def test_get_political_signal(client, mock_db):
    """GET /api/political/signal returns current signal."""
    row = make_political_signal_row()
    setup_scalar_one_or_none(mock_db, row)

    resp = client.get("/api/political/signal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["signal"] is not None
    assert data["signal"]["political_score"] == "0.2345"
    assert data["signal"]["next_event_type"] == "fomc_meeting"
    assert data["signal"]["news_volume_1h"] == 3
    assert data["signal"]["dominant_narrative"] == "crypto_regulation/sec"


def test_get_political_signal_none(client, mock_db):
    """Returns null when no signal computed."""
    setup_scalar_one_or_none(mock_db, None)

    resp = client.get("/api/political/signal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["signal"] is None
    assert "message" in data


def test_get_signal_history(client, mock_db):
    """GET /api/political/signal/history returns history with 'data' key."""
    rows = [make_political_signal_row(), make_political_signal_row()]
    setup_scalars_all(mock_db, rows)

    resp = client.get("/api/political/signal/history?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert data["data"][0]["political_score"] == "0.2345"


def test_get_signal_history_empty(client, mock_db):
    """Returns empty list when no signal history."""
    setup_scalars_all(mock_db, [])

    resp = client.get("/api/political/signal/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_get_narratives(client, mock_db):
    """GET /api/political/narratives returns active narratives."""
    with patch("app.services.political_narrative_service.detect_narratives") as mock_fn:
        mock_fn.return_value = [
            {
                "narrative": "crypto_regulation/sec",
                "article_count": 5,
                "avg_sentiment": 0.25,
                "velocity": 0.07,
                "direction": "bullish",
                "strength": 1.34,
            }
        ]
        resp = client.get("/api/political/narratives")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["data"][0]["narrative"] == "crypto_regulation/sec"
    assert data["data"][0]["direction"] == "bullish"


def test_get_narratives_empty(client, mock_db):
    """Returns empty list when no active narratives."""
    with patch("app.services.political_narrative_service.detect_narratives") as mock_fn:
        mock_fn.return_value = []
        resp = client.get("/api/political/narratives")

    assert resp.status_code == 200
    assert resp.json()["count"] == 0
