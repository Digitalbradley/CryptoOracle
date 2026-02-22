# CryptoOracle — MVP Product Requirements Document

## Esoteric Crypto Trading Intelligence Platform

**Version:** 1.0 MVP
**Author:** Brad
**Date:** February 2026
**Purpose:** Claude Code build specification for an MVP trading intelligence platform that layers traditional technical analysis with celestial, numerological, and gematria-based signal engines.

---

## 1. Product Vision

CryptoOracle is a personal crypto trading intelligence platform that combines traditional technical analysis, on-chain analytics, and esoteric signal layers (astrology, numerology, gematria) into a unified confluence scoring system. The platform monitors real-time market data, computes signals across all layers, and surfaces high-confluence alerts when multiple signal types align — enabling more informed, timing-aware trading decisions.

**Core Philosophy:** Every signal layer is treated as data. No layer is dismissed, no layer operates in isolation. The system backtests all layers against historical price action and lets the numbers determine how much weight each layer carries over time.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  Dashboard │ Alerts │ Backtest Results │ Cycle Calendar  │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API + WebSocket
┌─────────────────▼───────────────────────────────────────┐
│                 API SERVER (FastAPI)                      │
│  Routes │ WebSocket Manager │ Alert Engine │ Auth        │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              SIGNAL ENGINE (Python)                       │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │ Layer 1  │ │ Layer 2  │ │  Layer 3  │ │  Layer 4  │ │  Layer 5  │ │
│  │ Trad. TA │ │ On-Chain │ │ Celestial │ │ Sentiment │ │ Political │ │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ │
│       │            │             │              │              │        │
│       └────────────┴──────┬──────┴──────────────┴──────────────┘        │
│                           │                              │
│              ┌────────────▼─────────────┐                │
│              │  CONFLUENCE SCORER       │                │
│              │  Weighted composite score │                │
│              └────────────┬─────────────┘                │
│                           │                              │
│              ┌────────────▼─────────────┐                │
│              │  ALERT ENGINE            │                │
│              │  Threshold-based alerts   │                │
│              └──────────────────────────┘                │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              DATA LAYER                                  │
│  TimescaleDB (PostgreSQL) │ Redis (cache/pubsub)        │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              DATA INGESTION                              │
│  Exchange WebSockets │ On-Chain APIs │ Ephemeris Calc    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend API** | Python 3.11+ / FastAPI | Async, fast, great ecosystem for data/finance |
| **Database** | PostgreSQL + TimescaleDB | Time-series optimized, SQL-native, hypertables |
| **Cache/PubSub** | Redis | Real-time alert broadcasting, indicator caching |
| **Exchange Data** | `ccxt` library | Unified API for 100+ exchanges |
| **Technical Analysis** | `pandas-ta` or `ta-lib` | Comprehensive indicator library |
| **Ephemeris Engine** | `pyswisseph` (Swiss Ephemeris) | Industry-standard astronomical calculations |
| **Gematria Engine** | Custom Python module | Built from scratch — no existing libs meet needs |
| **Frontend** | React + Recharts + TailwindCSS | Real-time dashboard with chart visualization |
| **Task Scheduler** | APScheduler or Celery | Periodic data fetching, indicator computation |
| **Containerization** | Docker + Docker Compose | Reproducible dev/prod environment |

---

## 4. Database Schema

### 4.1 Core Market Data

```sql
-- TimescaleDB hypertable — this is the foundation everything reads from
CREATE TABLE price_data (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,          -- e.g., 'BTC/USDT'
    exchange VARCHAR(30) NOT NULL,         -- e.g., 'binance'
    timeframe VARCHAR(5) NOT NULL,         -- e.g., '1m', '5m', '1h', '1d'
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    PRIMARY KEY (timestamp, symbol, exchange, timeframe)
);

SELECT create_hypertable('price_data', 'timestamp');

CREATE INDEX idx_price_symbol_time ON price_data (symbol, timestamp DESC);
```

### 4.2 Technical Analysis Indicators

```sql
CREATE TABLE ta_indicators (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    -- Momentum
    rsi_14 DECIMAL(10, 4),
    rsi_7 DECIMAL(10, 4),
    macd_line DECIMAL(20, 8),
    macd_signal DECIMAL(20, 8),
    macd_histogram DECIMAL(20, 8),
    stoch_k DECIMAL(10, 4),
    stoch_d DECIMAL(10, 4),
    -- Trend
    sma_20 DECIMAL(20, 8),
    sma_50 DECIMAL(20, 8),
    sma_200 DECIMAL(20, 8),
    ema_12 DECIMAL(20, 8),
    ema_26 DECIMAL(20, 8),
    -- Volatility
    bb_upper DECIMAL(20, 8),
    bb_middle DECIMAL(20, 8),
    bb_lower DECIMAL(20, 8),
    atr_14 DECIMAL(20, 8),
    -- Fibonacci (calculated relative to recent swing high/low)
    fib_0 DECIMAL(20, 8),           -- swing low
    fib_236 DECIMAL(20, 8),
    fib_382 DECIMAL(20, 8),
    fib_500 DECIMAL(20, 8),
    fib_618 DECIMAL(20, 8),
    fib_786 DECIMAL(20, 8),
    fib_1000 DECIMAL(20, 8),        -- swing high
    -- Composite TA Score
    ta_score DECIMAL(5, 4),          -- -1.0 to +1.0
    PRIMARY KEY (timestamp, symbol, timeframe)
);

SELECT create_hypertable('ta_indicators', 'timestamp');
```

### 4.3 On-Chain Metrics

```sql
CREATE TABLE onchain_metrics (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    -- Exchange flows
    exchange_inflow DECIMAL(20, 8),
    exchange_outflow DECIMAL(20, 8),
    exchange_netflow DECIMAL(20, 8),
    -- Whale activity
    whale_transactions_count INTEGER,     -- tx > $100k
    whale_volume_usd DECIMAL(20, 2),
    -- Network health
    active_addresses INTEGER,
    hash_rate DECIMAL(20, 4),
    -- Holder behavior
    nupl DECIMAL(10, 6),                  -- Net Unrealized Profit/Loss
    mvrv_zscore DECIMAL(10, 6),
    sopr DECIMAL(10, 6),
    -- Composite Score
    onchain_score DECIMAL(5, 4),          -- -1.0 to +1.0
    PRIMARY KEY (timestamp, symbol)
);

SELECT create_hypertable('onchain_metrics', 'timestamp');
```

### 4.4 Celestial State (Ephemeris Data)

```sql
CREATE TABLE celestial_state (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,       -- computed daily at 00:00 UTC
    -- Lunar
    lunar_phase_angle DECIMAL(8, 4),      -- 0-360 degrees
    lunar_phase_name VARCHAR(20),          -- 'new_moon', 'waxing_crescent', etc.
    lunar_illumination DECIMAL(5, 4),     -- 0.0 to 1.0
    days_to_next_new_moon DECIMAL(6, 2),
    days_to_next_full_moon DECIMAL(6, 2),
    is_lunar_eclipse BOOLEAN DEFAULT FALSE,
    is_solar_eclipse BOOLEAN DEFAULT FALSE,
    -- Planetary Retrogrades (boolean flags)
    mercury_retrograde BOOLEAN DEFAULT FALSE,
    venus_retrograde BOOLEAN DEFAULT FALSE,
    mars_retrograde BOOLEAN DEFAULT FALSE,
    jupiter_retrograde BOOLEAN DEFAULT FALSE,
    saturn_retrograde BOOLEAN DEFAULT FALSE,
    retrograde_count INTEGER DEFAULT 0,   -- total planets in retrograde
    -- Planetary Positions (zodiac degrees 0-360)
    sun_longitude DECIMAL(8, 4),
    moon_longitude DECIMAL(8, 4),
    mercury_longitude DECIMAL(8, 4),
    venus_longitude DECIMAL(8, 4),
    mars_longitude DECIMAL(8, 4),
    jupiter_longitude DECIMAL(8, 4),
    saturn_longitude DECIMAL(8, 4),
    -- Active Aspects (stored as JSONB for flexibility)
    -- Format: [{"planet1": "mars", "planet2": "saturn", "aspect": "conjunction", "orb": 1.2}, ...]
    active_aspects JSONB DEFAULT '[]',
    -- Zodiac ingresses happening today
    ingresses JSONB DEFAULT '[]',         -- [{"planet": "mars", "sign": "aries", "type": "ingress"}]
    -- Composite celestial score
    celestial_score DECIMAL(5, 4),        -- -1.0 to +1.0
    PRIMARY KEY (timestamp)
);

SELECT create_hypertable('celestial_state', 'timestamp');
```

### 4.5 Numerology & Gematria

```sql
-- Stores the numerological properties of each date
CREATE TABLE numerology_daily (
    id BIGSERIAL,
    date DATE NOT NULL UNIQUE,
    -- Date numerology
    date_digit_sum INTEGER,               -- e.g., 2026-02-20 = 2+0+2+6+0+2+2+0 = 14 = 1+4 = 5
    is_master_number BOOLEAN DEFAULT FALSE, -- 11, 22, 33
    master_number_value INTEGER,           -- NULL or 11/22/33
    universal_day_number INTEGER,          -- final reduced digit 1-9 (or 11/22/33)
    -- Cycle tracking
    active_cycles JSONB DEFAULT '{}',     -- {"47_day": {"reference_event": "2025-10-10_crash", "day_number": 23, "days_remaining": 24}}
    cycle_confluence_count INTEGER DEFAULT 0, -- how many tracked cycles align on this date
    -- Number frequency in price
    price_47_appearances JSONB DEFAULT '[]', -- prices that contained "47" on this date
    -- Composite numerology score
    numerology_score DECIMAL(5, 4),       -- -1.0 to +1.0
    PRIMARY KEY (date)
);

-- Gematria reference table for crypto symbols and key terms
CREATE TABLE gematria_values (
    id SERIAL PRIMARY KEY,
    term VARCHAR(100) NOT NULL,            -- e.g., 'BITCOIN', 'BTC', 'ETHEREUM', 'SATOSHI NAKAMOTO'
    -- Multiple cipher values
    english_ordinal INTEGER,               -- A=1, B=2, ... Z=26
    full_reduction INTEGER,                -- reduced to single digit
    reverse_ordinal INTEGER,               -- A=26, B=25, ... Z=1
    reverse_reduction INTEGER,
    jewish_gematria INTEGER,
    english_gematria INTEGER,              -- A=6, B=12, ... (x6)
    -- Derived properties
    digit_sum INTEGER,                     -- sum of all digits in primary value
    is_prime BOOLEAN,
    associated_planet VARCHAR(20),          -- numerological planet association
    associated_element VARCHAR(20),         -- fire, water, earth, air
    notes TEXT,                            -- manual annotations
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(term)
);

-- Tracks custom numeric cycles the user defines
CREATE TABLE custom_cycles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,            -- e.g., '47-Day Crash Cycle'
    cycle_days INTEGER NOT NULL,           -- 47
    reference_date DATE NOT NULL,          -- anchor date for the cycle
    reference_event TEXT,                  -- 'BTC crash from $X to $Y'
    is_active BOOLEAN DEFAULT TRUE,
    hit_count INTEGER DEFAULT 0,           -- times this cycle aligned with actual events
    miss_count INTEGER DEFAULT 0,
    hit_rate DECIMAL(5, 4),               -- hit_count / (hit_count + miss_count)
    tolerance_days INTEGER DEFAULT 2,      -- +/- window for counting a "hit"
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.6 Sentiment

```sql
CREATE TABLE sentiment_data (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    -- Indices
    fear_greed_index INTEGER,             -- 0-100
    fear_greed_label VARCHAR(20),         -- 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'
    -- Social
    social_volume INTEGER,                -- mentions count
    social_sentiment DECIMAL(5, 4),       -- -1.0 to +1.0
    social_source VARCHAR(20),            -- 'twitter', 'reddit', 'aggregate'
    -- Google Trends
    google_trends_score INTEGER,          -- 0-100
    -- Composite sentiment score
    sentiment_score DECIMAL(5, 4),        -- -1.0 to +1.0
    PRIMARY KEY (timestamp, symbol)
);

SELECT create_hypertable('sentiment_data', 'timestamp');
```

### 4.7 Political Events & Macro Intelligence

```sql
-- Scheduled events known in advance (FOMC, hearings, elections, etc.)
CREATE TABLE political_calendar (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_time TIMESTAMPTZ,               -- NULL if all-day or time unknown
    event_type VARCHAR(50) NOT NULL,       -- 'fomc_meeting', 'congressional_hearing', 'executive_order',
                                           -- 'sec_ruling', 'election', 'regulatory_deadline',
                                           -- 'international_summit', 'tariff_announcement', 'sanctions'
    category VARCHAR(30) NOT NULL,         -- 'monetary_policy', 'crypto_regulation', 'trade_policy',
                                           -- 'geopolitical', 'election', 'fiscal_policy'
    title VARCHAR(300) NOT NULL,
    description TEXT,
    country VARCHAR(5) DEFAULT 'US',       -- ISO country code
    -- Impact assessment (can be pre-filled for known event types, updated after event)
    expected_volatility VARCHAR(10),       -- 'low', 'medium', 'high', 'extreme'
    expected_direction VARCHAR(10),        -- 'bullish', 'bearish', 'neutral', 'unknown'
    crypto_relevance INTEGER DEFAULT 5,   -- 1-10 scale, how directly this impacts crypto
    -- Post-event tracking
    actual_outcome TEXT,                   -- filled in after event occurs
    actual_price_impact_pct DECIMAL(10, 4), -- BTC move within 24h of event
    -- Esoteric cross-reference
    date_gematria_value INTEGER,           -- universal day number for this date
    key_figure_gematria JSONB,             -- {"Jerome Powell": {"ordinal": 168, "reduced": 6}}
    event_title_gematria JSONB,            -- gematria values of the event title
    -- Source
    source_url TEXT,
    source_name VARCHAR(100),
    is_recurring BOOLEAN DEFAULT FALSE,    -- e.g., FOMC meets 8x/year
    recurrence_rule TEXT,                  -- cron-like or description
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_polcal_date ON political_calendar (event_date);
CREATE INDEX idx_polcal_type ON political_calendar (event_type, event_date);
CREATE INDEX idx_polcal_category ON political_calendar (category, event_date);

-- Real-time news events (breaking news, surprise announcements)
CREATE TABLE political_news (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    -- Source info
    source_name VARCHAR(100) NOT NULL,     -- 'reuters', 'coindesk', 'whitehouse.gov', 'sec.gov'
    source_url TEXT,
    headline VARCHAR(500) NOT NULL,
    summary TEXT,                          -- first 2-3 sentences or AI-generated summary
    -- Classification (computed via Claude API or rules engine)
    category VARCHAR(30),                  -- same categories as political_calendar
    subcategory VARCHAR(50),               -- more specific: 'etf_approval', 'mining_ban', 'rate_hike'
    crypto_relevance_score DECIMAL(5, 4),  -- 0.0 to 1.0 (how relevant to crypto)
    sentiment_score DECIMAL(5, 4),         -- -1.0 to +1.0 (bearish to bullish for crypto)
    urgency_score DECIMAL(5, 4),           -- 0.0 to 1.0 (how time-sensitive)
    -- Key entities extracted
    entities JSONB,                        -- {"people": ["Jerome Powell"], "orgs": ["SEC", "Fed"],
                                           --  "countries": ["US", "CN"], "coins": ["BTC", "ETH"]}
    -- Gematria analysis of headline
    headline_gematria JSONB,               -- {"ordinal": 542, "reduced": 2, "key_words": {"bitcoin": 68}}
    -- Amplification tracking
    mention_velocity INTEGER,              -- mentions per hour on social media after publication
    mention_velocity_1h INTEGER,           -- velocity at 1 hour mark
    mention_velocity_4h INTEGER,           -- velocity at 4 hour mark
    peak_velocity INTEGER,
    peak_velocity_time TIMESTAMPTZ,
    -- Impact tracking
    btc_price_at_publish DECIMAL(20, 8),
    btc_price_1h_after DECIMAL(20, 8),
    btc_price_4h_after DECIMAL(20, 8),
    btc_price_24h_after DECIMAL(20, 8),
    actual_impact_pct DECIMAL(10, 4),      -- max move within 24h
    -- Composite political score
    political_score DECIMAL(5, 4),         -- -1.0 to +1.0
    PRIMARY KEY (timestamp, source_name, headline)
);

SELECT create_hypertable('political_news', 'timestamp');
CREATE INDEX idx_polnews_relevance ON political_news (crypto_relevance_score DESC, timestamp DESC);
CREATE INDEX idx_polnews_category ON political_news (category, timestamp DESC);

-- Aggregated political signal per time window
CREATE TABLE political_signal (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,        -- computed hourly
    -- Scheduled event proximity
    hours_to_next_major_event INTEGER,     -- NULL if none within 7 days
    next_event_type VARCHAR(50),
    next_event_expected_volatility VARCHAR(10),
    upcoming_events_7d INTEGER,            -- count of events in next 7 days
    upcoming_high_impact_7d INTEGER,       -- count of high/extreme volatility events in 7 days
    -- News flow analysis
    news_volume_1h INTEGER,                -- relevant articles in last hour
    news_volume_24h INTEGER,               -- relevant articles in last 24 hours
    avg_news_sentiment_1h DECIMAL(5, 4),   -- average sentiment of recent articles
    avg_news_sentiment_24h DECIMAL(5, 4),
    max_urgency_1h DECIMAL(5, 4),          -- most urgent article in last hour
    -- Narrative detection
    dominant_narrative VARCHAR(100),        -- AI-detected: 'etf_momentum', 'regulatory_crackdown', 'rate_cut_expectations'
    narrative_strength DECIMAL(5, 4),       -- 0.0 to 1.0
    narrative_direction VARCHAR(10),        -- 'bullish', 'bearish', 'neutral'
    -- Composite political score
    political_score DECIMAL(5, 4),         -- -1.0 to +1.0
    PRIMARY KEY (timestamp)
);

SELECT create_hypertable('political_signal', 'timestamp');
```

### 4.8 Confluence Scores

```sql
CREATE TABLE confluence_scores (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    -- Individual layer scores (-1.0 to +1.0)
    ta_score DECIMAL(5, 4),
    onchain_score DECIMAL(5, 4),
    celestial_score DECIMAL(5, 4),
    numerology_score DECIMAL(5, 4),
    sentiment_score DECIMAL(5, 4),
    political_score DECIMAL(5, 4),
    -- Weights used for this calculation
    weights JSONB NOT NULL,               -- {"ta": 0.25, "onchain": 0.20, "celestial": 0.15, "numerology": 0.10, "sentiment": 0.15, "political": 0.15}
    -- Composite
    composite_score DECIMAL(5, 4),        -- weighted sum, -1.0 to +1.0
    signal_strength VARCHAR(10),          -- 'strong_buy', 'buy', 'neutral', 'sell', 'strong_sell'
    -- Which layers are aligned
    aligned_layers JSONB,                 -- ["ta", "celestial", "numerology", "political"] — layers all pointing same direction
    alignment_count INTEGER,              -- number of aligned layers
    PRIMARY KEY (timestamp, symbol, timeframe)
);

SELECT create_hypertable('confluence_scores', 'timestamp');
```

### 4.9 Historical Events (for backtesting)

```sql
CREATE TABLE historical_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    event_type VARCHAR(30) NOT NULL,      -- 'crash', 'pump', 'halving', 'ath', 'cycle_low'
    magnitude_pct DECIMAL(10, 4),         -- percentage move
    price_at_event DECIMAL(20, 8),
    duration_hours INTEGER,               -- how long the move took
    -- Inter-event intervals (computed)
    days_since_previous_crash INTEGER,
    days_since_previous_pump INTEGER,
    days_since_previous_halving INTEGER,
    -- Celestial state at time of event
    lunar_phase_name VARCHAR(20),
    mercury_retrograde BOOLEAN,
    active_aspects_snapshot JSONB,
    -- Numerological state
    date_universal_number INTEGER,
    active_cycle_alignments JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_type_time ON historical_events (event_type, timestamp DESC);
CREATE INDEX idx_events_symbol ON historical_events (symbol, timestamp DESC);
```

### 4.9 Alerts

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    triggered_at TIMESTAMPTZ,
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(30) NOT NULL,      -- 'confluence', 'cycle_alignment', 'retrograde_start', 'price_level', 'custom'
    severity VARCHAR(10) NOT NULL,        -- 'info', 'warning', 'critical'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    -- What triggered it
    trigger_data JSONB,                   -- full context of what caused the alert
    composite_score DECIMAL(5, 4),
    aligned_layers JSONB,
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'acknowledged', 'dismissed'
    acknowledged_at TIMESTAMPTZ
);
```

### 4.10 User Configuration

```sql
CREATE TABLE signal_weights (
    id SERIAL PRIMARY KEY,
    profile_name VARCHAR(50) DEFAULT 'default',
    ta_weight DECIMAL(5, 4) DEFAULT 0.25,
    onchain_weight DECIMAL(5, 4) DEFAULT 0.20,
    celestial_weight DECIMAL(5, 4) DEFAULT 0.15,
    numerology_weight DECIMAL(5, 4) DEFAULT 0.10,
    sentiment_weight DECIMAL(5, 4) DEFAULT 0.15,
    political_weight DECIMAL(5, 4) DEFAULT 0.15,
    -- Weights must sum to 1.0
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE watched_symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,   -- 'BTC/USDT', 'ETH/USDT', 'XRP/USDT'
    exchange VARCHAR(30) DEFAULT 'binance',
    is_active BOOLEAN DEFAULT TRUE,
    timeframes JSONB DEFAULT '["1h", "4h", "1d"]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Signal Layer Specifications

### 5.1 Layer 1 — Traditional Technical Analysis

**Module:** `signals/technical.py`

**Inputs:** Price data (OHLCV)

**Indicators to compute:**
- RSI (7, 14 periods)
- MACD (12, 26, 9)
- Stochastic Oscillator (14, 3, 3)
- Bollinger Bands (20, 2)
- SMA (20, 50, 200)
- EMA (12, 26)
- ATR (14)
- Fibonacci retracement levels (auto-detect swing high/low using zigzag or N-bar lookback)
- Volume profile (relative volume vs 20-day average)

**Score Computation (-1.0 to +1.0):**
- RSI > 70 = bearish signal (-0.5 to -1.0 scaled by how far above 70)
- RSI < 30 = bullish signal (+0.5 to +1.0)
- MACD crossover = +/- 0.3
- Price below BB lower = bullish +0.3
- Golden cross (50 SMA > 200 SMA) = +0.4
- Death cross = -0.4
- Price at Fibonacci level = +/- 0.2 (with direction based on trend)
- Average all sub-signals with equal weight for composite ta_score

**Computation Frequency:** Every new candle close (1h default, configurable)

### 5.2 Layer 2 — On-Chain Analytics

**Module:** `signals/onchain.py`

**Data Sources (pick one to start, expand later):**
- CryptoQuant API (free tier available)
- Glassnode API
- Santiment API

**Metrics:**
- Exchange net flow (negative = bullish, coins leaving exchanges)
- Whale transaction count (>$100k)
- NUPL (Net Unrealized Profit/Loss) — above 0.75 = euphoria/bearish, below 0 = capitulation/bullish
- MVRV Z-Score — above 7 = overvalued, below 0 = undervalued
- SOPR — below 1 = selling at loss (capitulation)

**Score Computation:**
- Each metric maps to a -1 to +1 range
- Weighted average for composite onchain_score
- Default: equal weight across available metrics

**Computation Frequency:** Every 4 hours (on-chain data updates slowly)

### 5.3 Layer 3 — Celestial / Esoteric Engine

**Module:** `signals/celestial.py`

**Sub-module 3A — Astronomical Ephemeris:**

**Library:** `pyswisseph` (Python bindings for Swiss Ephemeris)

**Compute daily:**
1. **Lunar phase** — exact angle (0° = new moon, 180° = full moon)
2. **Planetary retrogrades** — Mercury, Venus, Mars, Jupiter, Saturn
3. **Planetary longitudes** — ecliptic longitude for each planet
4. **Aspects** — conjunction (0°), sextile (60°), square (90°), trine (120°), opposition (180°) with configurable orb (default 8° for major aspects)
5. **Eclipse dates** — flag lunar and solar eclipses
6. **Ingresses** — when planets change zodiac signs

**Astrological Score Rules (configurable, backtestable):**
- New moon: +0.2 (historically correlates with accumulation)
- Full moon: -0.2 (historically correlates with distribution)
- Mercury retrograde: -0.3 (increased volatility/reversals)
- Saturn-Jupiter conjunction: +/- 0.4 (major cycle shifts)
- Mars square Saturn: -0.3 (tension, conflict energy)
- Eclipse within 3 days: -0.4 (high volatility expected)
- Multiple retrogrades (3+): -0.5

**Sub-module 3B — Numerological Engine:**

**Module:** `signals/numerology.py`

**Date Numerology:**
```python
def universal_day_number(date):
    """
    Reduce a date to its universal day number.
    2026-02-20 -> 2+0+2+6+0+2+2+0 = 14 -> 1+4 = 5
    Preserve master numbers: 11, 22, 33
    """

def is_master_number_date(date):
    """Check if date reduces to 11, 22, or 33"""

def date_digit_sum(date):
    """Raw digit sum before reduction"""
```

**Custom Cycle Tracker:**
```python
class CycleTracker:
    """
    Tracks N-day cycles from reference events.
    Primary use case: the 47-day crash cycle.

    Methods:
    - add_cycle(name, days, reference_date, reference_event)
    - check_date(date) -> list of active cycle alignments
    - days_until_next(cycle_name) -> int
    - get_hit_rate(cycle_name) -> float
    """
```

**Gematria Calculator:**
```python
class GematriaCalculator:
    """
    Multiple cipher support:
    - English Ordinal: A=1, B=2, ... Z=26
    - Full Reduction: A=1, B=2, ... I=9, J=1, K=2, ...
    - Reverse Ordinal: A=26, B=25, ... Z=1
    - Reverse Reduction: reduced reverse
    - Jewish/Hebrew Gematria
    - English Gematria (x6 multiplier)

    Methods:
    - calculate(text, cipher='english_ordinal') -> int
    - calculate_all_ciphers(text) -> dict
    - find_matches(target_value, cipher) -> list of known terms
    - reduce_to_digit(number) -> int (with master number preservation)
    - analyze_price_level(price) -> dict of numerological properties
    """
```

**Price-Number Analysis:**
```python
def analyze_price_for_significance(price, watched_numbers=[47, 11, 22, 33, 7, 9, 13]):
    """
    Check if a price level contains or relates to significant numbers.
    - Does the price contain '47'? (e.g., $47,000 or $104,700)
    - Does the price digit-sum to a significant number?
    - Is the price at a round number that reduces to a key digit?
    """
```

**Numerology Score Rules:**
- Master number date (11, 22, 33): flag as high-energy day, +/- 0.2 based on other signals
- 47-day cycle alignment: -0.4 (bearish based on observed pattern)
- Multiple custom cycles aligning: multiply significance by overlap count
- Price at gematria-significant level: +/- 0.1 as support/resistance signal
- Universal day number matching gematria of active coin: +/- 0.15

**Computation Frequency:** Daily at 00:00 UTC, plus real-time price checks

### 5.4 Layer 4 — Sentiment

**Module:** `signals/sentiment.py`

**Data Sources:**
- Alternative.me Fear & Greed Index API (free)
- Optional: LunarCrush social metrics API
- Optional: Google Trends via `pytrends`

**Score Computation:**
- Fear & Greed < 20 (Extreme Fear): +0.8 (contrarian bullish)
- Fear & Greed 20-40: +0.3
- Fear & Greed 40-60: 0.0 (neutral)
- Fear & Greed 60-80: -0.3
- Fear & Greed > 80 (Extreme Greed): -0.8 (contrarian bearish)

**Computation Frequency:** Every 4 hours

### 5.5 Layer 5 — Political Events & Macro Intelligence

**Module:** `signals/political.py`

**Purpose:** Track scheduled political/economic events and real-time news that move crypto markets. Political events are unique because they have both a *pre-event* signal (known events create anticipatory volatility) and a *post-event* signal (the actual outcome and market reaction).

**Sub-module 5A — Political Calendar Engine:**

**Module:** `signals/political_calendar.py`

**Data Sources:**
- Economic calendar APIs: Investing.com calendar, ForexFactory, TradingEconomics API
- Government RSS feeds: whitehouse.gov, sec.gov, federalreserve.gov, congress.gov
- Crypto-specific: SEC EDGAR (crypto-related filings), CFTC announcements
- Manual entry for known upcoming events

**Pre-Seeded Recurring Events:**
```python
RECURRING_POLITICAL_EVENTS = [
    {"type": "fomc_meeting", "frequency": "8x/year", "volatility": "high", "category": "monetary_policy"},
    {"type": "cpi_release", "frequency": "monthly", "volatility": "high", "category": "monetary_policy"},
    {"type": "jobs_report", "frequency": "monthly", "volatility": "medium", "category": "fiscal_policy"},
    {"type": "gdp_release", "frequency": "quarterly", "volatility": "medium", "category": "fiscal_policy"},
    {"type": "sec_meeting", "frequency": "varies", "volatility": "high", "category": "crypto_regulation"},
    {"type": "treasury_refunding", "frequency": "quarterly", "volatility": "medium", "category": "monetary_policy"},
    {"type": "opec_meeting", "frequency": "~6x/year", "volatility": "medium", "category": "geopolitical"},
    {"type": "g7_g20_summit", "frequency": "annual", "volatility": "medium", "category": "geopolitical"},
    {"type": "us_election", "frequency": "2yr/4yr", "volatility": "extreme", "category": "election"},
    {"type": "debt_ceiling_deadline", "frequency": "irregular", "volatility": "extreme", "category": "fiscal_policy"},
]
```

**Calendar Score Rules:**
- Major event within 24 hours: increase volatility expectation, score = 0.0 (direction unknown) but flag as "high volatility zone"
- FOMC rate cut expected: +0.3 (liquidity bullish)
- FOMC rate hike expected: -0.3 (liquidity bearish)
- SEC crypto hearing scheduled: -0.2 (historically net bearish, regulatory uncertainty)
- Tariff announcement: -0.3 (risk-off)
- Election day within 7 days: flag "extreme uncertainty", widen alert thresholds
- Debt ceiling crisis: -0.5 (extreme risk-off)
- No major events within 7 days: +0.1 (calm macro = risk-on drift)

**Sub-module 5B — Real-Time News Classifier:**

**Module:** `signals/political_news.py`

**Data Sources (tiered by priority):**
- **Tier 1 — Official Sources:** Government press releases (SEC, Fed, White House). RSS feeds, scraped hourly.
- **Tier 2 — Wire Services:** Reuters, AP, Bloomberg headlines. NewsAPI.org (free tier: 100 requests/day) or GNews API.
- **Tier 3 — Crypto News:** CoinDesk, CoinTelegraph, The Block. RSS feeds or their APIs.
- **Tier 4 — Social Amplification:** X/Twitter via API for mention velocity tracking of key political terms.

**Classification Pipeline:**
```python
class PoliticalNewsClassifier:
    """
    For each incoming news article:

    1. RELEVANCE FILTER
       - Quick keyword scan: does it mention crypto, bitcoin, SEC, Fed, tariff,
         regulation, sanctions, digital assets, CBDC, stablecoin, etc.?
       - If no keywords: discard (don't waste API calls)
       - If keywords: proceed to classification

    2. AI CLASSIFICATION (Claude API)
       - Send headline + first 500 chars to Claude with structured prompt:
         "Classify this news article for crypto market impact:
          - crypto_relevance: 0.0-1.0
          - sentiment: -1.0 to +1.0 (bearish to bullish for crypto)
          - urgency: 0.0-1.0 (how time-sensitive)
          - category: [monetary_policy|crypto_regulation|trade_policy|geopolitical|election|fiscal_policy]
          - subcategory: [specific label]
          - entities: {people: [], orgs: [], countries: [], coins: []}
          - expected_impact_duration: [hours|days|weeks]
          Respond in JSON only."

    3. GEMATRIA ENRICHMENT
       - Run headline through GematriaCalculator
       - Run key entity names through GematriaCalculator
       - Store values for cross-reference with price levels

    4. AMPLIFICATION TRACKING (delayed, runs 1h and 4h after publish)
       - Count mentions of key terms from the article on social media
       - Track velocity: mentions/hour
       - High velocity + high relevance = stronger signal
       - Low velocity + high relevance = market hasn't priced it in yet (potential edge)

    5. IMPACT TRACKING (delayed, runs 1h, 4h, 24h after publish)
       - Record BTC price at each interval
       - Calculate actual impact percentage
       - Feed back into scoring model to improve future predictions
    """
```

**News Score Computation:**
```python
def compute_political_news_score(recent_articles, hours_window=24):
    """
    Aggregate recent political news into a single score.

    1. Filter to articles with crypto_relevance > 0.3
    2. Weight each article: sentiment * relevance * urgency * recency_decay
       - recency_decay: exponential decay, half-life = 6 hours
    3. Take weighted average of all articles
    4. Amplification multiplier: if mention_velocity > threshold, amplify by 1.5x
    5. Clamp to -1.0 to +1.0
    """
```

**Sub-module 5C — Narrative Detector:**

**Module:** `signals/political_narrative.py`

```python
class NarrativeDetector:
    """
    Identifies dominant political/macro narratives that persist over days/weeks.
    These are more important than individual news events because narratives
    drive sustained positioning.

    Known narrative patterns:
    - 'rate_cut_expectations': Fed dovish signals accumulating -> bullish crypto
    - 'regulatory_crackdown': SEC enforcement actions clustering -> bearish
    - 'etf_momentum': ETF approvals/filings -> bullish
    - 'trade_war_escalation': tariff announcements -> bearish risk-off
    - 'defi_regulation': specific DeFi targeting -> bearish for DeFi, may be neutral BTC
    - 'cbdc_progress': government digital currency news -> mixed, watch for 'ban private crypto' subnarrative
    - 'bipartisan_crypto_support': legislation with bipartisan backing -> bullish
    - 'stablecoin_regulation': clarity on stablecoins -> generally bullish (legitimizing)
    - 'mining_restrictions': energy/environmental focus -> bearish for mining, muted on BTC price
    - 'sovereign_adoption': countries adding BTC to reserves -> strongly bullish

    Process:
    1. Every 4 hours, analyze last 72 hours of classified news
    2. Cluster articles by category + subcategory
    3. If a cluster has 5+ articles with consistent direction -> active narrative
    4. Assign narrative_strength (based on article count + avg relevance)
    5. Assign narrative_direction (based on avg sentiment of cluster)
    6. Track narrative persistence: how many consecutive 4h windows has this narrative been active?
    7. Longer persistence = stronger signal weight
    """
```

**Composite Political Score:**
```python
def compute_political_score():
    """
    Combines all sub-modules:

    political_score = (
        0.30 * calendar_proximity_score +    # scheduled event impact
        0.35 * news_sentiment_score +         # real-time news flow
        0.35 * narrative_score                # persistent narrative direction
    )

    Special overrides:
    - If a "black swan" news item detected (urgency > 0.9, relevance > 0.9):
      override composite, set political_score = article sentiment * 0.8
    - If FOMC day: boost calendar_proximity_score weight to 0.50
    """
```

**Computation Frequency:**
- Calendar events: checked daily, countdowns updated hourly
- News classification: every 15-30 minutes (batch incoming articles)
- Narrative detection: every 4 hours
- Composite political_score: hourly

---

## 6. Confluence Scoring Engine

**Module:** `engine/confluence.py`

### 6.1 Score Computation

```python
class ConfluenceEngine:
    def compute_score(self, symbol, timestamp, weights=None):
        """
        1. Gather latest scores from each layer (TA, on-chain, celestial, numerology, sentiment, political)
        2. Apply weights (from signal_weights table or override)
        3. Compute weighted average
        4. Determine signal_strength label
        5. Identify aligned layers (all pointing same direction)
        6. Store result in confluence_scores table
        """

    def get_alignment(self, scores: dict) -> dict:
        """
        Determine which layers agree.
        If ta_score > 0.2 AND celestial_score > 0.2 AND political_score > 0.2,
        those three are 'aligned bullish'.
        High alignment count = higher conviction signal.
        Max possible alignment: 6/6 layers.
        """
```

### 6.2 Signal Strength Thresholds

| Composite Score | Label | Action Suggestion |
|----------------|-------|-------------------|
| +0.6 to +1.0 | `strong_buy` | High confluence bullish |
| +0.2 to +0.6 | `buy` | Moderate bullish |
| -0.2 to +0.2 | `neutral` | No clear signal |
| -0.6 to -0.2 | `sell` | Moderate bearish |
| -1.0 to -0.6 | `strong_sell` | High confluence bearish |

### 6.3 Alert Triggers

Generate an alert when:
1. **Confluence threshold crossed:** composite_score moves above +0.5 or below -0.5
2. **Layer alignment:** 4+ layers agree on direction (now out of 6 total)
3. **Cycle alignment:** A tracked custom cycle (e.g., 47-day) reaches its target date (+/- tolerance)
4. **Celestial event:** Mercury retrograde starts/ends, eclipse within 48 hours
5. **Extreme sentiment:** Fear & Greed < 10 or > 90
6. **Numerological date:** Master number date + other aligned signals
7. **Political black swan:** News article with urgency > 0.9 AND relevance > 0.9
8. **Major scheduled event:** High-impact political calendar event within 24 hours
9. **Narrative shift:** Dominant narrative changes direction (bullish -> bearish or vice versa)
10. **Esoteric-political confluence:** Major political event date has significant gematria value AND aligns with a custom cycle

---

## 7. Backtesting Module

**Module:** `engine/backtester.py`

### 7.1 The 47-Day Cycle Backtester (Priority #1)

```python
class CycleBacktester:
    """
    Purpose: Validate the 47-day (and other) crash cycle hypothesis.

    Process:
    1. Pull all BTC daily price data going back to 2015
    2. Identify all significant drops (configurable: >8%, >10%, >15% within 48-72 hours)
    3. Calculate day-count intervals between every pair of consecutive drops
    4. Statistical analysis:
       a. Frequency distribution of all intervals
       b. Highlight intervals that are multiples of 47 or within +/-2 of 47
       c. Chi-squared test: are 47-day intervals more frequent than expected by chance?
       d. Cross-reference with celestial state at each crash
       e. Cross-reference with numerological properties of each crash date
    5. Output: report with confidence score for the 47-day hypothesis
    """
```

### 7.2 General Signal Backtester

```python
class SignalBacktester:
    """
    For any signal layer or combination:
    1. Replay historical data day by day
    2. Compute what each layer's score would have been
    3. Track: if you acted on signals above threshold X, what would your P&L be?
    4. Optimize weights: which weight combination maximizes hit rate?

    Output: hit_rate, avg_return_on_signal, max_drawdown, sharpe_ratio_equivalent
    """
```

---

## 8. API Endpoints

### 8.1 Market Data
```
GET  /api/v1/price/{symbol}                    # Current price + recent candles
GET  /api/v1/price/{symbol}/history             # Historical OHLCV
WS   /ws/price/{symbol}                         # Real-time price stream
```

### 8.2 Signals
```
GET  /api/v1/signals/{symbol}                   # Current scores for all layers
GET  /api/v1/signals/{symbol}/history           # Historical signal scores
GET  /api/v1/signals/{symbol}/ta                # TA indicators detail
GET  /api/v1/signals/{symbol}/celestial         # Current celestial state
GET  /api/v1/signals/{symbol}/numerology        # Current numerological state
GET  /api/v1/signals/{symbol}/political         # Current political signal state
```

### 8.3 Confluence
```
GET  /api/v1/confluence/{symbol}                # Current composite score
GET  /api/v1/confluence/{symbol}/history        # Historical composite scores
POST /api/v1/confluence/weights                 # Update signal weights
GET  /api/v1/confluence/weights                 # Get current weights
```

### 8.4 Cycles & Gematria
```
GET  /api/v1/cycles                             # List all tracked cycles
POST /api/v1/cycles                             # Add a new cycle to track
GET  /api/v1/cycles/{id}/status                 # Current cycle day + next target date
GET  /api/v1/gematria/calculate                 # Calculate gematria for a term
GET  /api/v1/gematria/lookup/{value}            # Find terms matching a gematria value
GET  /api/v1/calendar                           # Upcoming celestial + numerological + political events
```

### 8.5 Political Events
```
GET  /api/v1/political/calendar                 # Upcoming scheduled political events
POST /api/v1/political/calendar                 # Manually add a political event
GET  /api/v1/political/news                     # Recent classified political news
GET  /api/v1/political/news/feed                # Raw news feed with classification
GET  /api/v1/political/narrative                # Current dominant narrative(s)
GET  /api/v1/political/narrative/history         # Narrative shifts over time
GET  /api/v1/political/score                    # Current composite political score
GET  /api/v1/political/gematria/{event_id}       # Gematria analysis of a specific event
WS   /ws/political/breaking                      # Real-time breaking political news stream
```

### 8.6 Backtesting
```
POST /api/v1/backtest/cycle                     # Run cycle backtester
POST /api/v1/backtest/signals                   # Run signal backtester
GET  /api/v1/backtest/results/{id}              # Get backtest results
```

### 8.6 Alerts
```
GET  /api/v1/alerts                             # List active alerts
POST /api/v1/alerts/{id}/acknowledge            # Acknowledge an alert
WS   /ws/alerts                                 # Real-time alert stream
```

---

## 9. Frontend Dashboard

### 9.0 Design Philosophy — Mobile-First "Celestial Terminal"

**Mobile-first approach.** The primary audience discovers CryptoOracle via social sharing (Twitter/X, Reddit, Telegram). That traffic is 80%+ mobile. Every view is designed for a 375px viewport first, then enhanced for tablet (768px) and desktop (1280px+). No horizontal scrolling. No tiny tap targets. Every interactive element is minimum 44px touch target.

**Design System — "Celestial Terminal"**

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-void` | `#0A0B0F` | Page background |
| `--bg-surface` | `#0F1117` | Card/panel background |
| `--bg-elevated` | `#161822` | Modals, dropdowns, hover states |
| `--border-subtle` | `#1E2030` | Card borders, dividers |
| `--border-active` | `#2A2D40` | Active/focused borders |
| `--text-primary` | `#E8E6E3` | Primary text |
| `--text-secondary` | `#8B8D98` | Labels, captions |
| `--text-muted` | `#545664` | Disabled, placeholder |
| `--accent-gold` | `#D4A846` | Primary accent, CTA, confluence highlight |
| `--accent-gold-dim` | `#D4A84633` | Gold glow, subtle backgrounds |
| **Layer Colors** | | |
| `--layer-ta` | `#5B8DEF` | Steel blue — Technical Analysis |
| `--layer-onchain` | `#9B6DFF` | Amethyst — On-Chain |
| `--layer-celestial` | `#D4A846` | Gold — Celestial |
| `--layer-numerology` | `#C77B4A` | Copper — Numerology |
| `--layer-sentiment` | `#4ECDC4` | Seafoam — Sentiment |
| `--layer-political` | `#E85D75` | Rose — Political |
| **Signal Colors** | | |
| `--signal-bullish` | `#22C55E` | Green — positive scores |
| `--signal-bearish` | `#EF4444` | Red — negative scores |
| `--signal-neutral` | `#8B8D98` | Grey — neutral zone |
| **Severity Colors** | | |
| `--severity-critical` | `#EF4444` | Critical alerts |
| `--severity-warning` | `#F59E0B` | Warning alerts |
| `--severity-info` | `#3B82F6` | Info alerts |

**Typography:**
- UI text: `Inter` (system fallback: `-apple-system, BlinkMacSystemFont, sans-serif`)
- Numbers/data: `JetBrains Mono` — monospace prevents layout jitter as values update
- Sizes: `text-xs` (12px) for captions, `text-sm` (14px) for body, `text-base` (16px) for labels, `text-lg`+ for hero numbers

**Interaction Patterns:**
- Bottom navigation on mobile (5 tabs: Dashboard, Alerts, Calendar, Tools, Settings)
- Pull-to-refresh on main dashboard (triggers API refetch)
- Swipeable cards for layer breakdown details
- Tap-to-expand for compact data panels
- No hover-dependent interactions (everything works on touch)

### 9.1 Mobile Layout — Main Dashboard (375px)

The mobile dashboard is a vertical card stack. Each card is a self-contained information unit that can be scanned in 2-3 seconds. The user scrolls vertically through the signal layers.

```
┌─────────────────────────────┐
│ ☽ CryptoOracle    BTC ▾  ⚙ │  ← Sticky header: logo, symbol picker, settings
├─────────────────────────────┤
│                             │
│  ┌─────────────────────────┐│
│  │     CONFLUENCE SCORE    ││  ← Hero card: the single most important element
│  │                         ││
│  │    ◉ +0.62  STRONG BUY ││     Radial gauge, large score, signal label
│  │    ═══════════●══       ││     Color-coded: green/red/grey
│  │                         ││
│  │  Aligned: 5/6 layers ▸  ││     Tap to expand layer breakdown
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  BTC/USDT  $98,420.50  ││  ← Price card: current price + sparkline
│  │  ▲ +2.4% (24h)         ││     Mini candlestick chart (last 24h)
│  │  ▁▂▃▅▆▇█▆▅▇█▇▆▅▃▅▆▇█  ││     Tap to expand full chart view
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  LAYER BREAKDOWN        ││  ← 6 horizontal bars, color-coded by layer
│  │  TA         ██████░  +0.45 │  Steel blue
│  │  On-Chain   █████████ +0.70 │  Amethyst
│  │  Celestial  ███████░  +0.55 │  Gold
│  │  Numerology ██████████+0.80 │  Copper
│  │  Sentiment  ████████░ +0.60 │  Seafoam
│  │  Political  █████░░░  +0.35 │  Rose
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  ACTIVE ALERTS  (3) ▸   ││  ← Alert summary card
│  │  ● 47-Day Cycle: Day 43 ││     Severity dot + compact text
│  │  ● FOMC Meeting: 2 days ││     Tap to expand or go to Alerts tab
│  │  ● F&G: 22 Extreme Fear ││
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  CELESTIAL STATE        ││  ← Moon phase visual + key data
│  │  ☾ Waxing Gibbous  82% ││     Moon emoji/icon + illumination %
│  │  ☿ Retro: No  ♂□♄     ││     Compact aspect display
│  │  Universal Day: #5      ││
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  POLITICAL PULSE        ││  ← Political summary card
│  │  Next: FOMC Mar 18 (2d) ││     Next major event + countdown
│  │  Narrative: Rate Cut ▲  ││     Dominant narrative + direction
│  │  News: 15 articles (24h)││     Volume indicator
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  CYCLE TRACKER          ││  ← Compact cycle cards
│  │  47-Day  ██████████░ 43/47 ⚠ │  Progress bar + status
│  │  Lunar   ████░░░░░░ 12/29   │
│  │  33-Day  ██░░░░░░░░  8/33   │
│  └─────────────────────────┘│
│                             │
├─────────────────────────────┤
│ 📊  🔔  📅  🔧  ⚙        │  ← Bottom nav: Dashboard, Alerts, Calendar,
│ Home Alert Cal  Tool  Set  │     Tools, Settings
└─────────────────────────────┘
```

### 9.2 Mobile Layout — Expanded Views

**Full Price Chart (tap price card or rotate to landscape):**
```
┌─────────────────────────────┐
│  ← BTC/USDT    1h 4h 1d ▾ │  ← Back button, timeframe pills
│                             │
│  ┌─────────────────────────┐│
│  │                         ││
│  │   TradingView-style     ││     Full-width lightweight-charts
│  │   Candlestick Chart     ││     Touch: pinch-to-zoom, pan
│  │   (lightweight-charts)  ││     Height: 60vh on mobile
│  │                         ││
│  │                         ││
│  └─────────────────────────┘│
│                             │
│  Overlays:                  │
│  [RSI] [BB] [MA] [Fib] [Vol]│  ← Toggle pills for TA overlays
│                             │
│  TA Score: +0.45            │
│  RSI(14): 58.2  MACD: +450 │  ← Key TA values below chart
└─────────────────────────────┘
```

**Layer Detail (tap any layer bar):**
```
┌─────────────────────────────┐
│  ← Technical Analysis       │
│  Score: +0.45               │
│                             │
│  RSI(14)     58.2    Neutral│  ← Individual indicator breakdown
│  RSI(7)      70.1    ▲ High│
│  MACD        +450    Bullish│
│  Stoch K/D   75/72   ▲ High│
│  BB Position  Mid    Neutral│
│  SMA Cross   Golden  Bullish│
│  Fib Level   0.618   Support│
│                             │
│  Score History (7d):        │
│  ▁▂▃▅▃▅▆▅▃▅▆▇▅▆▅▃▅▆▇      │  ← Sparkline of score over time
└─────────────────────────────┘
```

**Alerts Tab:**
```
┌─────────────────────────────┐
│  Alerts          Filter ▾   │
│                             │
│  TODAY                      │
│  ┌─────────────────────────┐│
│  │ ● CRITICAL              ││
│  │ 47-Day Cycle: Day 43/47 ││  ← Full alert card with severity
│  │ BTC/USDT • 2 hours ago  ││     badge, description, timestamp
│  │ Cycle alignment within  ││
│  │ tolerance window...     ││
│  │          [Acknowledge]  ││  ← Action button
│  └─────────────────────────┘│
│  ┌─────────────────────────┐│
│  │ ● WARNING               ││
│  │ FOMC Meeting in 2 days  ││
│  │ BTC/USDT • 6 hours ago  ││
│  │ High-impact political...││
│  └─────────────────────────┘│
│                             │
│  YESTERDAY                  │
│  ┌─────────────────────────┐│
│  │ ● INFO                  ││
│  │ Layer alignment: 5/6    ││
│  └─────────────────────────┘│
└─────────────────────────────┘
```

**Calendar Tab:**
```
┌─────────────────────────────┐
│  Calendar         Mar 2026  │
│  ◀  ●●●●●●●●●●●●●●●●● ▶   │  ← Horizontal month scroller
│                             │
│  ┌─M─┬─T─┬─W─┬─T─┬─F─┬─S─┐│
│  │   │   │   │   │   │   ││  ← Compact month grid
│  │ 1 │ 2 │ 3●│ 4 │ 5 │ 6 ││     Dots indicate events
│  │ 7 │ 8 │ 9 │10 │11◆│12●││     ● = celestial  ◆ = political
│  │13 │14 │15★│16 │17◆│18◆││     ★ = cycle alignment  ○ = numerology
│  │...                      ││
│  └─────────────────────────┘│
│                             │
│  Mar 15 — Events:           │
│  ★ 47-Day Cycle hit         │  ← Tap a date to see events below
│  ○ Master Number Date (33)  │
│  ● Full Moon                │
│  ◆ CPI Release (high vol.)  │
└─────────────────────────────┘
```

**Tools Tab — Gematria Calculator:**
```
┌─────────────────────────────┐
│  Gematria Calculator        │
│                             │
│  [  Enter text...        ]  │  ← Input field
│                             │
│  "BITCOIN"                  │
│  ┌─────────────────────────┐│
│  │ English Ordinal:    77  ││
│  │ Full Reduction:     32  ││  ← All cipher values
│  │ Reverse Ordinal:   103  ││
│  │ Reverse Reduction:  40  ││
│  │ Jewish Gematria:   429  ││
│  │ English Gematria:  462  ││
│  │ Digit Sum:           5  ││
│  │ Is Prime:          Yes  ││
│  │ Planet:        Mercury  ││
│  │ Element:           Air  ││
│  └─────────────────────────┘│
│                             │
│  Matching terms at 77:      │
│  • "CHRIST", "POWER"       │  ← Cross-reference matches
└─────────────────────────────┘
```

**Settings Tab — Weight Tuner:**
```
┌─────────────────────────────┐
│  Signal Weights             │
│  Profile: default ▾        │
│                             │
│  Technical Analysis   0.25  │
│  ═══════════●═══════        │  ← Full-width sliders
│                             │
│  On-Chain            0.20   │
│  ════════●══════════        │
│                             │
│  Celestial           0.15   │
│  ══════●════════════        │
│                             │
│  Numerology          0.10   │
│  ════●══════════════        │
│                             │
│  Sentiment           0.15   │
│  ══════●════════════        │
│                             │
│  Political           0.15   │
│  ══════●════════════        │
│                             │
│  Total: 1.00 ✓              │
│                             │
│  [  Save Weights  ]         │  ← Validates sum = 1.0
└─────────────────────────────┘
```

### 9.3 Desktop Layout (1280px+)

On desktop, the vertical card stack becomes a two-column layout. Left column is the price chart (60% width, full viewport height). Right column is a scrollable stack of signal panels.

```
┌──────────────────────────────────────────────────────────────────────┐
│ ☽ CryptoOracle           BTC/USDT ▾  ETH  XRP     🔔 3   ⚙       │
├────────────────────────────────────────┬─────────────────────────────┤
│                                        │  CONFLUENCE SCORE           │
│                                        │  ◉ +0.62  STRONG BUY       │
│   Price Chart (lightweight-charts)     │  ═══════════●══             │
│   Full-height candlestick              │  Aligned: 5/6 layers       │
│   with TA overlay toggles              │                             │
│                                        ├─────────────────────────────┤
│   [1h] [4h] [1d]                       │  LAYER BREAKDOWN            │
│   [RSI] [BB] [MA] [Fib] [Vol]         │  TA        ██████░░  +0.45 │
│                                        │  On-Chain  █████████  +0.70 │
│                                        │  Celestial ███████░░  +0.55 │
│                                        │  Numerology██████████ +0.80 │
│                                        │  Sentiment ████████░  +0.60 │
│                                        │  Political █████░░░░  +0.35 │
│                                        ├─────────────────────────────┤
│                                        │  ACTIVE ALERTS (3)          │
│                                        │  ● 47-Day Cycle: Day 43/47 │
│                                        │  ● FOMC Meeting: 2 days    │
│                                        │  ● F&G: 22 Extreme Fear    │
│                                        ├─────────────────────────────┤
│                                        │  CELESTIAL  │  POLITICAL    │
│                                        │  ☾ Wax Gib  │  FOMC: 2d    │
│                                        │  ☿ No Retro │  Rate Cut ▲  │
│                                        │  Day: #5    │  News: 15    │
├────────────────────────────────────────┼─────────────────────────────┤
│  CYCLE TRACKER                                                       │
│  47-Day ██████████░ 43/47 ⚠   Lunar ████░░░░ 12/29   33-Day ██░ 8/33│
└──────────────────────────────────────────────────────────────────────┘
```

**Desktop enhancements over mobile:**
- Sidebar navigation replaces bottom tabs
- Celestial + Political panels displayed side-by-side
- Cycle tracker shown as horizontal row instead of stacked cards
- Price chart is always visible (sticky left column)
- Layer bars are clickable — clicking opens a detail popover inline instead of navigating away

### 9.4 Data Fetching Strategy

**Phase 5 — Polling (no WebSocket needed):**
- Dashboard auto-refreshes every 60 seconds via `setInterval` + Axios
- Pull-to-refresh triggers immediate refetch on mobile
- Individual panels can be manually refreshed (tap refresh icon)
- `react-query` (TanStack Query) for cache, deduplication, stale-while-revalidate
- API calls: `GET /api/confluence/{symbol}`, `GET /api/alerts`, `GET /api/celestial`, etc.

**Phase 6 — WebSocket upgrade (deferred):**
- Add Redis pub/sub backend
- Socket.io for real-time alert push + price updates
- Replace polling with push for alerts and price data
- Confluence score updates remain polling (hourly computation cycle)

### 9.5 Responsive Breakpoints

| Breakpoint | Width | Layout | Navigation |
|-----------|-------|--------|------------|
| Mobile | < 768px | Single column, card stack | Bottom tab bar (5 tabs) |
| Tablet | 768-1279px | Two columns, collapsed panels | Bottom tab bar or side rail |
| Desktop | >= 1280px | Two columns, all panels visible | Left sidebar |

### 9.6 Component Architecture

```
src/
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx          # Responsive shell: header + nav + content area
│   │   ├── BottomNav.tsx         # Mobile bottom tab bar
│   │   ├── Sidebar.tsx           # Desktop left sidebar
│   │   └── Header.tsx            # Sticky header with symbol picker
│   ├── dashboard/
│   │   ├── ConfluenceGauge.tsx   # Hero radial gauge (-1.0 to +1.0)
│   │   ├── PriceCard.tsx         # Current price + sparkline + 24h change
│   │   ├── LayerBreakdown.tsx    # 6 horizontal score bars
│   │   ├── AlertSummary.tsx      # Compact alert list (3 most recent)
│   │   ├── CelestialCard.tsx     # Moon phase + retrogrades + aspects
│   │   ├── PoliticalCard.tsx     # Next event + narrative + news volume
│   │   └── CycleTracker.tsx      # Progress bars for tracked cycles
│   ├── chart/
│   │   ├── PriceChart.tsx        # lightweight-charts wrapper
│   │   ├── ChartOverlays.tsx     # TA indicator toggle pills
│   │   └── ScoreSparkline.tsx    # Mini sparkline for score history
│   ├── alerts/
│   │   ├── AlertList.tsx         # Full alert list with filters
│   │   ├── AlertCard.tsx         # Individual alert with actions
│   │   └── AlertFilters.tsx      # Severity/type filter pills
│   ├── calendar/
│   │   ├── CalendarGrid.tsx      # Month grid with event dots
│   │   ├── DayDetail.tsx         # Events for selected date
│   │   └── EventBadge.tsx        # Colored dot/icon per event type
│   ├── tools/
│   │   ├── GematriaCalc.tsx      # Interactive gematria calculator
│   │   ├── WeightTuner.tsx       # 6 sliders + save button
│   │   └── BacktestViewer.tsx    # Backtest results display
│   └── shared/
│       ├── ScoreBar.tsx          # Reusable horizontal score bar
│       ├── SeverityBadge.tsx     # Colored severity pill
│       ├── SymbolPicker.tsx      # Symbol dropdown selector
│       └── PullToRefresh.tsx     # Mobile pull-to-refresh wrapper
├── hooks/
│   ├── useConfluence.ts          # TanStack Query hook for confluence data
│   ├── useAlerts.ts              # Query hook for alerts
│   ├── useCelestial.ts           # Query hook for celestial state
│   ├── usePolitical.ts           # Query hook for political signal
│   ├── usePrice.ts               # Query hook for price data
│   └── useAutoRefresh.ts         # 60-second polling manager
├── lib/
│   ├── api.ts                    # Axios instance + base URL config
│   ├── colors.ts                 # Layer/signal/severity color constants
│   └── format.ts                 # Number formatters (scores, prices, percentages)
├── pages/
│   ├── DashboardPage.tsx         # Main dashboard (card stack / 2-column)
│   ├── AlertsPage.tsx            # Full alerts list
│   ├── CalendarPage.tsx          # Event calendar
│   ├── ToolsPage.tsx             # Gematria calc + weight tuner
│   └── SettingsPage.tsx          # App settings
└── App.tsx                       # Router + QueryProvider + theme
```

### 9.7 Tech Stack (Frontend)

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `react` | ^18 | UI framework |
| `react-router-dom` | ^6 | Client-side routing (5 pages) |
| `@tanstack/react-query` | ^5 | Data fetching, caching, polling |
| `axios` | ^1.7 | HTTP client |
| `tailwindcss` | ^3.4 | Utility-first CSS (mobile-first breakpoints) |
| `lightweight-charts` | ^4.1 | TradingView candlestick charts |
| `recharts` | ^2.10 | Score history sparklines, backtest charts |
| `lucide-react` | ^0.300 | Icon library (lightweight, tree-shakeable) |

**Not needed in Phase 5:** `socket.io-client` (deferred to Phase 6 WebSocket upgrade)

### 9.8 Additional Views

- **Backtest Results:** Bar charts showing cycle hit rates, signal accuracy over time (Recharts)
- **Historical Events Map:** Timeline of crashes/pumps with celestial + numerological state overlaid (Phase 6)

---

## 10. MVP Build Phases

### Phase 1 — Foundation (Week 1-2)
**Goal:** Data pipeline running, basic TA signals, database populated

- [ ] Project scaffolding: FastAPI app, Docker Compose (Postgres+TimescaleDB, Redis)
- [ ] Database migrations (all tables from Section 4)
- [ ] CCXT integration: fetch and store BTC/USDT, ETH/USDT, XRP/USDT historical daily data from Binance (at least back to 2017)
- [ ] TA indicator computation module using `pandas-ta`
- [ ] Basic scheduler: fetch new candles every hour, compute TA indicators
- [ ] Seed `historical_events` table with known BTC crashes (>10% drops) — manually curate from price data

### Phase 2 — Esoteric Engines (Week 3-4)
**Goal:** Celestial and numerology layers operational

- [ ] Swiss Ephemeris integration (`pyswisseph`)
- [ ] Daily celestial state computation: lunar phase, retrogrades, aspects, eclipses
- [ ] Backfill celestial_state table for all historical dates (2015-present)
- [ ] Gematria calculator module with multiple ciphers
- [ ] Numerology daily computation: universal day numbers, master number flags
- [ ] Custom cycle tracker: implement 47-day cycle + ability to add more
- [ ] Backfill numerology_daily table
- [ ] Cross-reference historical_events with celestial + numerological state

### Phase 3 — Confluence & Backtesting (Week 5-6)
**Goal:** All layers scoring, backtester validating

- [ ] Sentiment module: Fear & Greed Index API integration
- [ ] On-chain module: CryptoQuant or Glassnode free tier integration
- [ ] Confluence scoring engine: weighted composite + alignment detection (6 layers)
- [ ] 47-Day Cycle Backtester: statistical validation with full report output
- [ ] General signal backtester: replay historical data, compute hypothetical signals
- [ ] Weight optimization: brute-force or grid search for optimal layer weights
- [ ] Alert engine: threshold-based alert generation + storage

### Phase 4 — Political Events Layer (Week 7-8)
**Goal:** Political intelligence fully integrated as Layer 5

- [ ] Political calendar engine: seed with recurring events (FOMC, CPI, etc.)
- [ ] Government RSS feed integration (SEC, Fed, White House, Congress)
- [ ] NewsAPI or GNews integration for real-time headline ingestion
- [ ] Claude API classification pipeline: relevance, sentiment, urgency scoring
- [ ] Gematria enrichment of political events (headline + key figure analysis)
- [ ] Amplification tracking: social mention velocity after major news
- [ ] Impact tracking: record BTC price at 1h/4h/24h after political news
- [ ] Narrative detector: cluster analysis of recent political news
- [ ] Composite political_score computation
- [ ] Backfill: classify major historical political events (2020-present) and correlate with price action
- [ ] Add political_score to confluence engine

### Phase 5 — Frontend Dashboard (Week 9-10)
**Goal:** Mobile-first responsive dashboard with polling-based data

- [ ] React app scaffolding: Vite + React 18 + TailwindCSS + React Router
- [ ] Design system: CSS custom properties for Celestial Terminal theme (colors, typography)
- [ ] AppShell layout: responsive shell with sticky header, bottom nav (mobile), sidebar (desktop)
- [ ] API layer: Axios instance + TanStack Query hooks with 60-second auto-refresh
- [ ] Confluence gauge: hero radial/arc gauge component (-1.0 to +1.0, color-coded)
- [ ] Price card: current price + 24h change + sparkline (lightweight-charts mini chart)
- [ ] Layer breakdown: 6 horizontal score bars with layer-specific colors
- [ ] Full price chart page: lightweight-charts candlestick with TA overlay toggle pills
- [ ] Alert summary card (dashboard) + full alert list page with severity filters
- [ ] Celestial state card: moon phase, retrogrades, aspects, universal day number
- [ ] Political pulse card: next event countdown, dominant narrative, news volume
- [ ] Cycle tracker: progress bars with status indicators
- [ ] Calendar page: month grid with event-type dots + tap-to-expand day detail
- [ ] Gematria calculator: input field + all cipher values + cross-reference matches
- [ ] Weight tuner: 6 sliders with sum validation + save to API
- [ ] CORS configuration on FastAPI backend for frontend origin
- [ ] Build + deploy configuration (Vite build, static hosting or Railway service)

### Phase 6 — Polish & Extend (Week 11-12)
**Goal:** Real-time push, polish, expandability

- [ ] WebSocket upgrade: Redis pub/sub + Socket.io for real-time alerts + price push
- [ ] Historical event timeline with overlaid celestial/numerological/political state
- [ ] Political event impact scorecard: compare expected vs actual impact over time
- [ ] Additional symbols support (easy add via watched_symbols)
- [ ] Email/SMS/push alert notifications (PWA push notifications for mobile)
- [ ] Multiple weight profiles (aggressive, conservative, esoteric-heavy, macro-heavy)
- [ ] Export data to CSV
- [ ] PWA manifest + service worker for mobile "Add to Home Screen"
- [ ] Documentation and README

---

## 11. MVP Configuration Defaults

```json
{
  "watched_symbols": ["BTC/USDT", "ETH/USDT", "XRP/USDT"],
  "default_exchange": "binance",
  "default_timeframes": ["1h", "4h", "1d"],
  "signal_weights": {
    "ta": 0.25,
    "onchain": 0.20,
    "celestial": 0.15,
    "numerology": 0.10,
    "sentiment": 0.15,
    "political": 0.15
  },
  "alert_thresholds": {
    "confluence_high": 0.5,
    "confluence_low": -0.5,
    "min_aligned_layers": 4,
    "cycle_proximity_days": 3
  },
  "custom_cycles": [
    {
      "name": "47-Day Crash Cycle",
      "days": 47,
      "tolerance": 2,
      "direction": "bearish"
    }
  ],
  "watched_numbers": [7, 9, 11, 13, 22, 33, 47],
  "aspect_orb_degrees": 8,
  "ta_indicators": {
    "rsi_periods": [7, 14],
    "macd": [12, 26, 9],
    "bb_period": 20,
    "bb_std": 2,
    "sma_periods": [20, 50, 200],
    "ema_periods": [12, 26],
    "atr_period": 14
  }
}
```

---

## 12. Key Dependencies

```
# requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0
alembic>=1.12
psycopg2-binary>=2.9
redis>=5.0
ccxt>=4.1
pandas>=2.1
pandas-ta>=0.3
numpy>=1.25
pyswisseph>=2.10
apscheduler>=3.10
httpx>=0.25
websockets>=12.0
pydantic>=2.5
python-dotenv>=1.0
feedparser>=6.0                # RSS feed parsing for gov/news sources
newsapi-python>=0.2            # NewsAPI.org client
anthropic>=0.40                # Claude API for news classification
beautifulsoup4>=4.12           # HTML parsing for web scraping
lxml>=5.0                      # Fast XML/HTML parser
```

```
# package.json (frontend)
{
  "dependencies": {
    "react": "^18",
    "react-dom": "^18",
    "react-router-dom": "^6",
    "@tanstack/react-query": "^5",
    "axios": "^1.7",
    "recharts": "^2.10",
    "lightweight-charts": "^4.1",
    "lucide-react": "^0.300"
  },
  "devDependencies": {
    "tailwindcss": "^3.4",
    "autoprefixer": "^10",
    "postcss": "^8",
    "vite": "^5",
    "@vitejs/plugin-react": "^4"
  }
}
```

---

## 13. Environment Variables

```env
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/cryptooracle
REDIS_URL=redis://localhost:6379
EXCHANGE_API_KEY=              # Optional: for higher rate limits
EXCHANGE_API_SECRET=
CRYPTOQUANT_API_KEY=           # On-chain data
ALTERNATIVE_ME_API=            # Fear & Greed (free, no key needed)
LUNARCRUSH_API_KEY=            # Optional: social sentiment
NEWSAPI_KEY=                   # NewsAPI.org for headline ingestion
ANTHROPIC_API_KEY=             # Claude API for news classification + gematria analysis
GNEWS_API_KEY=                 # Optional: GNews as backup news source
ALERT_EMAIL=                   # Optional: email notifications
```

---

## 14. Notes for Claude Code

- **Start with Phase 1.** Get the data pipeline and database working first. Everything else depends on good historical data.
- **The 47-day cycle backtester is the highest-priority unique feature.** Prioritize getting enough historical crash data to validate or invalidate this pattern with statistical rigor.
- **Swiss Ephemeris requires the ephemeris data files.** Download the Swiss Ephemeris data files (freely available) and include them in the Docker image or mount them as a volume.
- **All scores use -1.0 to +1.0 range.** This normalization is critical for the confluence engine to work properly across heterogeneous signal types.
- **Every scoring rule should be configurable via the database or config file.** The user will want to tune rules like "Mercury retrograde = -0.3" based on backtest results.
- **Build the gematria calculator as a standalone module** that can be imported and used independently — it's useful outside the trading context too.
- **The political layer uses Claude's API for classification.** Keep API calls efficient — batch articles when possible, use short structured prompts that request JSON output only. Cache classification results so you never re-classify the same headline.
- **Political calendar events should be pre-seeded.** On first run, populate the political_calendar table with known 2026 FOMC dates, CPI release dates, and other scheduled macro events. These are available from the Fed's website and economic calendar sites.
- **RSS feeds are the cheapest news source.** Start with government RSS feeds (sec.gov, federalreserve.gov) and crypto news RSS (CoinDesk, CoinTelegraph) before paying for NewsAPI. Most news sites publish RSS feeds that can be parsed with `feedparser`.
- **The narrative detector is high value but can be Phase 4.** Individual news classification is more important in MVP; narrative detection adds the persistent trend layer that makes the political signal much more powerful over time.
- **Gematria enrichment of political events is a unique cross-layer feature.** When a political event's date, title, or key figure's name carries gematria significance that aligns with the numerology layer, flag it as a compound signal. This is something no other trading platform does.
- **The frontend is Phase 5 for a reason.** The backend intelligence is what matters. A beautiful dashboard with bad signals is useless. Get the signals right first.
- **Use Alembic for database migrations** from the start. Schema will evolve.
- **Log everything.** Every signal computation, every alert trigger, every API call, every news classification. You'll need this for debugging and backtesting validation.
- **Impact tracking is what makes the political layer self-improving.** By recording BTC price at 1h/4h/24h after each classified article, you build a training set that reveals which types of political events actually move crypto and which are noise. Over time, this feedback loop makes the political_score increasingly accurate.

---

*This PRD is designed to be consumed by Claude Code for iterative development. Each phase can be built, tested, and validated independently before moving to the next.*