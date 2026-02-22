"""Shared test fixtures for CryptoOracle API tests.

Provides a mock database session and TestClient so that tests
never touch the real database.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture()
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    return db


@pytest.fixture()
def client(mock_db):
    """TestClient with the DB dependency overridden to use mock_db."""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers — build mock ORM-like objects with attribute access
# ---------------------------------------------------------------------------

def make_price_row(**overrides):
    row = MagicMock()
    defaults = {
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "symbol": "BTC/USDT",
        "exchange": "kraken",
        "timeframe": "1h",
        "open": Decimal("45000.12345678"),
        "high": Decimal("45500.00000000"),
        "low": Decimal("44900.50000000"),
        "close": Decimal("45200.87654321"),
        "volume": Decimal("1234.56789012"),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_ta_row(**overrides):
    row = MagicMock()
    defaults = {
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "rsi_14": Decimal("65.2345"),
        "rsi_7": Decimal("70.1234"),
        "macd_line": Decimal("450.123"),
        "macd_signal": Decimal("440.876"),
        "macd_histogram": Decimal("9.247"),
        "stoch_k": Decimal("75.54"),
        "stoch_d": Decimal("72.12"),
        "sma_20": Decimal("45000.12"),
        "sma_50": Decimal("44500.87"),
        "sma_200": Decimal("44000.12"),
        "ema_12": Decimal("45100.12"),
        "ema_26": Decimal("44900.87"),
        "bb_upper": Decimal("45500.00"),
        "bb_middle": Decimal("45000.00"),
        "bb_lower": Decimal("44500.00"),
        "atr_14": Decimal("250.12"),
        "fib_0": Decimal("44000.00"),
        "fib_236": Decimal("44167.50"),
        "fib_382": Decimal("44333.33"),
        "fib_500": Decimal("44500.00"),
        "fib_618": Decimal("44666.67"),
        "fib_786": Decimal("44833.33"),
        "fib_1000": Decimal("45000.00"),
        "ta_score": Decimal("0.7234"),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_celestial_row(**overrides):
    row = MagicMock()
    defaults = {
        "timestamp": datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
        "lunar_phase_angle": Decimal("123.45"),
        "lunar_phase_name": "Waxing Gibbous",
        "lunar_illumination": Decimal("0.8234"),
        "days_to_next_new_moon": Decimal("7.50"),
        "days_to_next_full_moon": Decimal("14.25"),
        "is_lunar_eclipse": False,
        "is_solar_eclipse": False,
        "mercury_retrograde": False,
        "venus_retrograde": False,
        "mars_retrograde": False,
        "jupiter_retrograde": False,
        "saturn_retrograde": False,
        "retrograde_count": 0,
        "sun_longitude": Decimal("332.45"),
        "moon_longitude": Decimal("45.67"),
        "mercury_longitude": Decimal("310.12"),
        "venus_longitude": Decimal("298.76"),
        "mars_longitude": Decimal("125.43"),
        "jupiter_longitude": Decimal("240.12"),
        "saturn_longitude": Decimal("295.67"),
        "active_aspects": [{"type": "trine", "bodies": ["Sun", "Jupiter"]}],
        "ingresses": [],
        "celestial_score": Decimal("0.6234"),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_numerology_row(**overrides):
    row = MagicMock()
    defaults = {
        "date": date(2026, 1, 15),
        "date_digit_sum": 15,
        "is_master_number": False,
        "master_number_value": None,
        "universal_day_number": 6,
        "active_cycles": {"47_day": True},
        "cycle_confluence_count": 1,
        "price_47_appearances": [],
        "numerology_score": Decimal("0.5234"),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_gematria_row(**overrides):
    row = MagicMock()
    defaults = {
        "term": "bitcoin",
        "english_ordinal": 77,
        "full_reduction": 32,
        "reverse_ordinal": 103,
        "reverse_reduction": 40,
        "jewish_gematria": 429,
        "english_gematria": 462,
        "digit_sum": 5,
        "is_prime": True,
        "associated_planet": "Mercury",
        "associated_element": "Air",
        "notes": "Primary crypto reference",
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_sentiment_row(**overrides):
    row = MagicMock()
    defaults = {
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "symbol": "BTC/USDT",
        "fear_greed_index": 68,
        "fear_greed_label": "Greed",
        "sentiment_score": Decimal("-0.3100"),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_onchain_row(**overrides):
    row = MagicMock()
    defaults = {
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "symbol": "BTC/USDT",
        "exchange_inflow": Decimal("1234.56"),
        "exchange_outflow": Decimal("2345.67"),
        "exchange_netflow": Decimal("-1111.11"),
        "whale_transactions_count": 45,
        "whale_volume_usd": Decimal("1234567890.12"),
        "active_addresses": 567890,
        "nupl": Decimal("0.2345"),
        "mvrv_zscore": Decimal("1.2345"),
        "sopr": Decimal("1.0012"),
        "onchain_score": Decimal("0.2345"),
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_confluence_row(**overrides):
    row = MagicMock()
    defaults = {
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "ta_score": Decimal("0.7000"),
        "onchain_score": Decimal("0.2000"),
        "celestial_score": Decimal("0.5000"),
        "numerology_score": Decimal("0.3000"),
        "sentiment_score": Decimal("-0.2000"),
        "political_score": None,
        "weights": {"ta": 0.25, "celestial": 0.15},
        "composite_score": Decimal("0.3500"),
        "signal_strength": "buy",
        "aligned_layers": {"direction": "bullish", "layers": ["ta", "celestial"]},
        "alignment_count": 3,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_alert_row(**overrides):
    row = MagicMock()
    defaults = {
        "id": 1,
        "created_at": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
        "triggered_at": datetime(2026, 1, 15, 12, 5, tzinfo=timezone.utc),
        "symbol": "BTC/USDT",
        "alert_type": "confluence",
        "severity": "warning",
        "title": "High confluence bullish: BTC/USDT (+0.6234)",
        "description": "Composite score +0.6234 crossed +0.5 threshold.",
        "composite_score": Decimal("0.6234"),
        "aligned_layers": {"direction": "bullish", "layers": ["ta", "celestial"]},
        "trigger_data": {"composite_score": 0.6234},
        "status": "active",
        "acknowledged_at": None,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


def make_signal_weights_row(**overrides):
    row = MagicMock()
    defaults = {
        "id": 1,
        "profile_name": "default",
        "ta_weight": Decimal("0.2500"),
        "onchain_weight": Decimal("0.2000"),
        "celestial_weight": Decimal("0.1500"),
        "numerology_weight": Decimal("0.1000"),
        "sentiment_weight": Decimal("0.1500"),
        "political_weight": Decimal("0.1500"),
        "is_active": True,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


# ---------------------------------------------------------------------------
# Helper to wire mock_db to return rows from scalars().all() or
# scalar_one_or_none() chains
# ---------------------------------------------------------------------------

def setup_scalars_all(mock_db, rows):
    """Configure mock_db.execute(...).scalars().all() to return `rows`."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    mock_db.execute.return_value = result


def setup_scalar_one_or_none(mock_db, row):
    """Configure mock_db.execute(...).scalar_one_or_none() to return `row`."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    mock_db.execute.return_value = result
