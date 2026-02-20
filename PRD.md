\# CryptoOracle — MVP Product Requirements Document



\## Esoteric Crypto Trading Intelligence Platform



\*\*Version:\*\* 1.0 MVP

\*\*Author:\*\* Brad

\*\*Date:\*\* February 2026

\*\*Purpose:\*\* Claude Code build specification for an MVP trading intelligence platform that layers traditional technical analysis with celestial, numerological, and gematria-based signal engines.



---



\## 1. Product Vision



CryptoOracle is a personal crypto trading intelligence platform that combines traditional technical analysis, on-chain analytics, and esoteric signal layers (astrology, numerology, gematria) into a unified confluence scoring system. The platform monitors real-time market data, computes signals across all layers, and surfaces high-confluence alerts when multiple signal types align — enabling more informed, timing-aware trading decisions.



\*\*Core Philosophy:\*\* Every signal layer is treated as data. No layer is dismissed, no layer operates in isolation. The system backtests all layers against historical price action and lets the numbers determine how much weight each layer carries over time.



---



\## 2. Architecture Overview



```

┌─────────────────────────────────────────────────────────┐

│                    FRONTEND (React)                      │

│  Dashboard │ Alerts │ Backtest Results │ Cycle Calendar  │

└─────────────────┬───────────────────────────────────────┘

&nbsp;                 │ REST API + WebSocket

┌─────────────────▼───────────────────────────────────────┐

│                 API SERVER (FastAPI)                      │

│  Routes │ WebSocket Manager │ Alert Engine │ Auth        │

└─────────────────┬───────────────────────────────────────┘

&nbsp;                 │

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

&nbsp;                 │

┌─────────────────▼───────────────────────────────────────┐

│              DATA LAYER                                  │

│  TimescaleDB (PostgreSQL) │ Redis (cache/pubsub)        │

└─────────────────┬───────────────────────────────────────┘

&nbsp;                 │

┌─────────────────▼───────────────────────────────────────┐

│              DATA INGESTION                              │

│  Exchange WebSockets │ On-Chain APIs │ Ephemeris Calc    │

└─────────────────────────────────────────────────────────┘

```



---



\## 3. Tech Stack



| Component | Technology | Rationale |

|-----------|-----------|-----------|

| \*\*Backend API\*\* | Python 3.11+ / FastAPI | Async, fast, great ecosystem for data/finance |

| \*\*Database\*\* | PostgreSQL + TimescaleDB | Time-series optimized, SQL-native, hypertables |

| \*\*Cache/PubSub\*\* | Redis | Real-time alert broadcasting, indicator caching |

| \*\*Exchange Data\*\* | `ccxt` library | Unified API for 100+ exchanges |

| \*\*Technical Analysis\*\* | `pandas-ta` or `ta-lib` | Comprehensive indicator library |

| \*\*Ephemeris Engine\*\* | `pyswisseph` (Swiss Ephemeris) | Industry-standard astronomical calculations |

| \*\*Gematria Engine\*\* | Custom Python module | Built from scratch — no existing libs meet needs |

| \*\*Frontend\*\* | React + Recharts + TailwindCSS | Real-time dashboard with chart visualization |

| \*\*Task Scheduler\*\* | APScheduler or Celery | Periodic data fetching, indicator computation |

| \*\*Containerization\*\* | Docker + Docker Compose | Reproducible dev/prod environment |



---



\## 4. Database Schema



\### 4.1 Core Market Data



```sql

-- TimescaleDB hypertable — this is the foundation everything reads from

CREATE TABLE price\_data (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   symbol VARCHAR(20) NOT NULL,          -- e.g., 'BTC/USDT'

&nbsp;   exchange VARCHAR(30) NOT NULL,         -- e.g., 'binance'

&nbsp;   timeframe VARCHAR(5) NOT NULL,         -- e.g., '1m', '5m', '1h', '1d'

&nbsp;   open DECIMAL(20, 8),

&nbsp;   high DECIMAL(20, 8),

&nbsp;   low DECIMAL(20, 8),

&nbsp;   close DECIMAL(20, 8),

&nbsp;   volume DECIMAL(20, 8),

&nbsp;   PRIMARY KEY (timestamp, symbol, exchange, timeframe)

);



SELECT create\_hypertable('price\_data', 'timestamp');



CREATE INDEX idx\_price\_symbol\_time ON price\_data (symbol, timestamp DESC);

```



\### 4.2 Technical Analysis Indicators



```sql

CREATE TABLE ta\_indicators (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   symbol VARCHAR(20) NOT NULL,

&nbsp;   timeframe VARCHAR(5) NOT NULL,

&nbsp;   -- Momentum

&nbsp;   rsi\_14 DECIMAL(10, 4),

&nbsp;   rsi\_7 DECIMAL(10, 4),

&nbsp;   macd\_line DECIMAL(20, 8),

&nbsp;   macd\_signal DECIMAL(20, 8),

&nbsp;   macd\_histogram DECIMAL(20, 8),

&nbsp;   stoch\_k DECIMAL(10, 4),

&nbsp;   stoch\_d DECIMAL(10, 4),

&nbsp;   -- Trend

&nbsp;   sma\_20 DECIMAL(20, 8),

&nbsp;   sma\_50 DECIMAL(20, 8),

&nbsp;   sma\_200 DECIMAL(20, 8),

&nbsp;   ema\_12 DECIMAL(20, 8),

&nbsp;   ema\_26 DECIMAL(20, 8),

&nbsp;   -- Volatility

&nbsp;   bb\_upper DECIMAL(20, 8),

&nbsp;   bb\_middle DECIMAL(20, 8),

&nbsp;   bb\_lower DECIMAL(20, 8),

&nbsp;   atr\_14 DECIMAL(20, 8),

&nbsp;   -- Fibonacci (calculated relative to recent swing high/low)

&nbsp;   fib\_0 DECIMAL(20, 8),           -- swing low

&nbsp;   fib\_236 DECIMAL(20, 8),

&nbsp;   fib\_382 DECIMAL(20, 8),

&nbsp;   fib\_500 DECIMAL(20, 8),

&nbsp;   fib\_618 DECIMAL(20, 8),

&nbsp;   fib\_786 DECIMAL(20, 8),

&nbsp;   fib\_1000 DECIMAL(20, 8),        -- swing high

&nbsp;   -- Composite TA Score

&nbsp;   ta\_score DECIMAL(5, 4),          -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (timestamp, symbol, timeframe)

);



SELECT create\_hypertable('ta\_indicators', 'timestamp');

```



\### 4.3 On-Chain Metrics



```sql

CREATE TABLE onchain\_metrics (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   symbol VARCHAR(20) NOT NULL,

&nbsp;   -- Exchange flows

&nbsp;   exchange\_inflow DECIMAL(20, 8),

&nbsp;   exchange\_outflow DECIMAL(20, 8),

&nbsp;   exchange\_netflow DECIMAL(20, 8),

&nbsp;   -- Whale activity

&nbsp;   whale\_transactions\_count INTEGER,     -- tx > $100k

&nbsp;   whale\_volume\_usd DECIMAL(20, 2),

&nbsp;   -- Network health

&nbsp;   active\_addresses INTEGER,

&nbsp;   hash\_rate DECIMAL(20, 4),

&nbsp;   -- Holder behavior

&nbsp;   nupl DECIMAL(10, 6),                  -- Net Unrealized Profit/Loss

&nbsp;   mvrv\_zscore DECIMAL(10, 6),

&nbsp;   sopr DECIMAL(10, 6),

&nbsp;   -- Composite Score

&nbsp;   onchain\_score DECIMAL(5, 4),          -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (timestamp, symbol)

);



SELECT create\_hypertable('onchain\_metrics', 'timestamp');

```



\### 4.4 Celestial State (Ephemeris Data)



```sql

CREATE TABLE celestial\_state (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,       -- computed daily at 00:00 UTC

&nbsp;   -- Lunar

&nbsp;   lunar\_phase\_angle DECIMAL(8, 4),      -- 0-360 degrees

&nbsp;   lunar\_phase\_name VARCHAR(20),          -- 'new\_moon', 'waxing\_crescent', etc.

&nbsp;   lunar\_illumination DECIMAL(5, 4),     -- 0.0 to 1.0

&nbsp;   days\_to\_next\_new\_moon DECIMAL(6, 2),

&nbsp;   days\_to\_next\_full\_moon DECIMAL(6, 2),

&nbsp;   is\_lunar\_eclipse BOOLEAN DEFAULT FALSE,

&nbsp;   is\_solar\_eclipse BOOLEAN DEFAULT FALSE,

&nbsp;   -- Planetary Retrogrades (boolean flags)

&nbsp;   mercury\_retrograde BOOLEAN DEFAULT FALSE,

&nbsp;   venus\_retrograde BOOLEAN DEFAULT FALSE,

&nbsp;   mars\_retrograde BOOLEAN DEFAULT FALSE,

&nbsp;   jupiter\_retrograde BOOLEAN DEFAULT FALSE,

&nbsp;   saturn\_retrograde BOOLEAN DEFAULT FALSE,

&nbsp;   retrograde\_count INTEGER DEFAULT 0,   -- total planets in retrograde

&nbsp;   -- Planetary Positions (zodiac degrees 0-360)

&nbsp;   sun\_longitude DECIMAL(8, 4),

&nbsp;   moon\_longitude DECIMAL(8, 4),

&nbsp;   mercury\_longitude DECIMAL(8, 4),

&nbsp;   venus\_longitude DECIMAL(8, 4),

&nbsp;   mars\_longitude DECIMAL(8, 4),

&nbsp;   jupiter\_longitude DECIMAL(8, 4),

&nbsp;   saturn\_longitude DECIMAL(8, 4),

&nbsp;   -- Active Aspects (stored as JSONB for flexibility)

&nbsp;   -- Format: \[{"planet1": "mars", "planet2": "saturn", "aspect": "conjunction", "orb": 1.2}, ...]

&nbsp;   active\_aspects JSONB DEFAULT '\[]',

&nbsp;   -- Zodiac ingresses happening today

&nbsp;   ingresses JSONB DEFAULT '\[]',         -- \[{"planet": "mars", "sign": "aries", "type": "ingress"}]

&nbsp;   -- Composite celestial score

&nbsp;   celestial\_score DECIMAL(5, 4),        -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (timestamp)

);



SELECT create\_hypertable('celestial\_state', 'timestamp');

```



\### 4.5 Numerology \& Gematria



```sql

-- Stores the numerological properties of each date

CREATE TABLE numerology\_daily (

&nbsp;   id BIGSERIAL,

&nbsp;   date DATE NOT NULL UNIQUE,

&nbsp;   -- Date numerology

&nbsp;   date\_digit\_sum INTEGER,               -- e.g., 2026-02-20 = 2+0+2+6+0+2+2+0 = 14 = 1+4 = 5

&nbsp;   is\_master\_number BOOLEAN DEFAULT FALSE, -- 11, 22, 33

&nbsp;   master\_number\_value INTEGER,           -- NULL or 11/22/33

&nbsp;   universal\_day\_number INTEGER,          -- final reduced digit 1-9 (or 11/22/33)

&nbsp;   -- Cycle tracking

&nbsp;   active\_cycles JSONB DEFAULT '{}',     -- {"47\_day": {"reference\_event": "2025-10-10\_crash", "day\_number": 23, "days\_remaining": 24}}

&nbsp;   cycle\_confluence\_count INTEGER DEFAULT 0, -- how many tracked cycles align on this date

&nbsp;   -- Number frequency in price

&nbsp;   price\_47\_appearances JSONB DEFAULT '\[]', -- prices that contained "47" on this date

&nbsp;   -- Composite numerology score

&nbsp;   numerology\_score DECIMAL(5, 4),       -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (date)

);



-- Gematria reference table for crypto symbols and key terms

CREATE TABLE gematria\_values (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   term VARCHAR(100) NOT NULL,            -- e.g., 'BITCOIN', 'BTC', 'ETHEREUM', 'SATOSHI NAKAMOTO'

&nbsp;   -- Multiple cipher values

&nbsp;   english\_ordinal INTEGER,               -- A=1, B=2, ... Z=26

&nbsp;   full\_reduction INTEGER,                -- reduced to single digit

&nbsp;   reverse\_ordinal INTEGER,               -- A=26, B=25, ... Z=1

&nbsp;   reverse\_reduction INTEGER,

&nbsp;   jewish\_gematria INTEGER,

&nbsp;   english\_gematria INTEGER,              -- A=6, B=12, ... (x6)

&nbsp;   -- Derived properties

&nbsp;   digit\_sum INTEGER,                     -- sum of all digits in primary value

&nbsp;   is\_prime BOOLEAN,

&nbsp;   associated\_planet VARCHAR(20),          -- numerological planet association

&nbsp;   associated\_element VARCHAR(20),         -- fire, water, earth, air

&nbsp;   notes TEXT,                            -- manual annotations

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW(),

&nbsp;   UNIQUE(term)

);



-- Tracks custom numeric cycles the user defines

CREATE TABLE custom\_cycles (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   name VARCHAR(100) NOT NULL,            -- e.g., '47-Day Crash Cycle'

&nbsp;   cycle\_days INTEGER NOT NULL,           -- 47

&nbsp;   reference\_date DATE NOT NULL,          -- anchor date for the cycle

&nbsp;   reference\_event TEXT,                  -- 'BTC crash from $X to $Y'

&nbsp;   is\_active BOOLEAN DEFAULT TRUE,

&nbsp;   hit\_count INTEGER DEFAULT 0,           -- times this cycle aligned with actual events

&nbsp;   miss\_count INTEGER DEFAULT 0,

&nbsp;   hit\_rate DECIMAL(5, 4),               -- hit\_count / (hit\_count + miss\_count)

&nbsp;   tolerance\_days INTEGER DEFAULT 2,      -- +/- window for counting a "hit"

&nbsp;   notes TEXT,

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW()

);

```



\### 4.6 Sentiment



```sql

CREATE TABLE sentiment\_data (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   symbol VARCHAR(20) NOT NULL,

&nbsp;   -- Indices

&nbsp;   fear\_greed\_index INTEGER,             -- 0-100

&nbsp;   fear\_greed\_label VARCHAR(20),         -- 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'

&nbsp;   -- Social

&nbsp;   social\_volume INTEGER,                -- mentions count

&nbsp;   social\_sentiment DECIMAL(5, 4),       -- -1.0 to +1.0

&nbsp;   social\_source VARCHAR(20),            -- 'twitter', 'reddit', 'aggregate'

&nbsp;   -- Google Trends

&nbsp;   google\_trends\_score INTEGER,          -- 0-100

&nbsp;   -- Composite sentiment score

&nbsp;   sentiment\_score DECIMAL(5, 4),        -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (timestamp, symbol)

);



SELECT create\_hypertable('sentiment\_data', 'timestamp');

```



\### 4.7 Political Events \& Macro Intelligence



```sql

-- Scheduled events known in advance (FOMC, hearings, elections, etc.)

CREATE TABLE political\_calendar (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   event\_date DATE NOT NULL,

&nbsp;   event\_time TIMESTAMPTZ,               -- NULL if all-day or time unknown

&nbsp;   event\_type VARCHAR(50) NOT NULL,       -- 'fomc\_meeting', 'congressional\_hearing', 'executive\_order',

&nbsp;                                          -- 'sec\_ruling', 'election', 'regulatory\_deadline',

&nbsp;                                          -- 'international\_summit', 'tariff\_announcement', 'sanctions'

&nbsp;   category VARCHAR(30) NOT NULL,         -- 'monetary\_policy', 'crypto\_regulation', 'trade\_policy',

&nbsp;                                          -- 'geopolitical', 'election', 'fiscal\_policy'

&nbsp;   title VARCHAR(300) NOT NULL,

&nbsp;   description TEXT,

&nbsp;   country VARCHAR(5) DEFAULT 'US',       -- ISO country code

&nbsp;   -- Impact assessment (can be pre-filled for known event types, updated after event)

&nbsp;   expected\_volatility VARCHAR(10),       -- 'low', 'medium', 'high', 'extreme'

&nbsp;   expected\_direction VARCHAR(10),        -- 'bullish', 'bearish', 'neutral', 'unknown'

&nbsp;   crypto\_relevance INTEGER DEFAULT 5,   -- 1-10 scale, how directly this impacts crypto

&nbsp;   -- Post-event tracking

&nbsp;   actual\_outcome TEXT,                   -- filled in after event occurs

&nbsp;   actual\_price\_impact\_pct DECIMAL(10, 4), -- BTC move within 24h of event

&nbsp;   -- Esoteric cross-reference

&nbsp;   date\_gematria\_value INTEGER,           -- universal day number for this date

&nbsp;   key\_figure\_gematria JSONB,             -- {"Jerome Powell": {"ordinal": 168, "reduced": 6}}

&nbsp;   event\_title\_gematria JSONB,            -- gematria values of the event title

&nbsp;   -- Source

&nbsp;   source\_url TEXT,

&nbsp;   source\_name VARCHAR(100),

&nbsp;   is\_recurring BOOLEAN DEFAULT FALSE,    -- e.g., FOMC meets 8x/year

&nbsp;   recurrence\_rule TEXT,                  -- cron-like or description

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW(),

&nbsp;   updated\_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX idx\_polcal\_date ON political\_calendar (event\_date);

CREATE INDEX idx\_polcal\_type ON political\_calendar (event\_type, event\_date);

CREATE INDEX idx\_polcal\_category ON political\_calendar (category, event\_date);



-- Real-time news events (breaking news, surprise announcements)

CREATE TABLE political\_news (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   -- Source info

&nbsp;   source\_name VARCHAR(100) NOT NULL,     -- 'reuters', 'coindesk', 'whitehouse.gov', 'sec.gov'

&nbsp;   source\_url TEXT,

&nbsp;   headline VARCHAR(500) NOT NULL,

&nbsp;   summary TEXT,                          -- first 2-3 sentences or AI-generated summary

&nbsp;   -- Classification (computed via Claude API or rules engine)

&nbsp;   category VARCHAR(30),                  -- same categories as political\_calendar

&nbsp;   subcategory VARCHAR(50),               -- more specific: 'etf\_approval', 'mining\_ban', 'rate\_hike'

&nbsp;   crypto\_relevance\_score DECIMAL(5, 4),  -- 0.0 to 1.0 (how relevant to crypto)

&nbsp;   sentiment\_score DECIMAL(5, 4),         -- -1.0 to +1.0 (bearish to bullish for crypto)

&nbsp;   urgency\_score DECIMAL(5, 4),           -- 0.0 to 1.0 (how time-sensitive)

&nbsp;   -- Key entities extracted

&nbsp;   entities JSONB,                        -- {"people": \["Jerome Powell"], "orgs": \["SEC", "Fed"],

&nbsp;                                          --  "countries": \["US", "CN"], "coins": \["BTC", "ETH"]}

&nbsp;   -- Gematria analysis of headline

&nbsp;   headline\_gematria JSONB,               -- {"ordinal": 542, "reduced": 2, "key\_words": {"bitcoin": 68}}

&nbsp;   -- Amplification tracking

&nbsp;   mention\_velocity INTEGER,              -- mentions per hour on social media after publication

&nbsp;   mention\_velocity\_1h INTEGER,           -- velocity at 1 hour mark

&nbsp;   mention\_velocity\_4h INTEGER,           -- velocity at 4 hour mark

&nbsp;   peak\_velocity INTEGER,

&nbsp;   peak\_velocity\_time TIMESTAMPTZ,

&nbsp;   -- Impact tracking

&nbsp;   btc\_price\_at\_publish DECIMAL(20, 8),

&nbsp;   btc\_price\_1h\_after DECIMAL(20, 8),

&nbsp;   btc\_price\_4h\_after DECIMAL(20, 8),

&nbsp;   btc\_price\_24h\_after DECIMAL(20, 8),

&nbsp;   actual\_impact\_pct DECIMAL(10, 4),      -- max move within 24h

&nbsp;   -- Composite political score

&nbsp;   political\_score DECIMAL(5, 4),         -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (timestamp, source\_name, headline)

);



SELECT create\_hypertable('political\_news', 'timestamp');

CREATE INDEX idx\_polnews\_relevance ON political\_news (crypto\_relevance\_score DESC, timestamp DESC);

CREATE INDEX idx\_polnews\_category ON political\_news (category, timestamp DESC);



-- Aggregated political signal per time window

CREATE TABLE political\_signal (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,        -- computed hourly

&nbsp;   -- Scheduled event proximity

&nbsp;   hours\_to\_next\_major\_event INTEGER,     -- NULL if none within 7 days

&nbsp;   next\_event\_type VARCHAR(50),

&nbsp;   next\_event\_expected\_volatility VARCHAR(10),

&nbsp;   upcoming\_events\_7d INTEGER,            -- count of events in next 7 days

&nbsp;   upcoming\_high\_impact\_7d INTEGER,       -- count of high/extreme volatility events in 7 days

&nbsp;   -- News flow analysis

&nbsp;   news\_volume\_1h INTEGER,                -- relevant articles in last hour

&nbsp;   news\_volume\_24h INTEGER,               -- relevant articles in last 24 hours

&nbsp;   avg\_news\_sentiment\_1h DECIMAL(5, 4),   -- average sentiment of recent articles

&nbsp;   avg\_news\_sentiment\_24h DECIMAL(5, 4),

&nbsp;   max\_urgency\_1h DECIMAL(5, 4),          -- most urgent article in last hour

&nbsp;   -- Narrative detection

&nbsp;   dominant\_narrative VARCHAR(100),        -- AI-detected: 'etf\_momentum', 'regulatory\_crackdown', 'rate\_cut\_expectations'

&nbsp;   narrative\_strength DECIMAL(5, 4),       -- 0.0 to 1.0

&nbsp;   narrative\_direction VARCHAR(10),        -- 'bullish', 'bearish', 'neutral'

&nbsp;   -- Composite political score

&nbsp;   political\_score DECIMAL(5, 4),         -- -1.0 to +1.0

&nbsp;   PRIMARY KEY (timestamp)

);



SELECT create\_hypertable('political\_signal', 'timestamp');

```



\### 4.8 Confluence Scores



```sql

CREATE TABLE confluence\_scores (

&nbsp;   id BIGSERIAL,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   symbol VARCHAR(20) NOT NULL,

&nbsp;   timeframe VARCHAR(5) NOT NULL,

&nbsp;   -- Individual layer scores (-1.0 to +1.0)

&nbsp;   ta\_score DECIMAL(5, 4),

&nbsp;   onchain\_score DECIMAL(5, 4),

&nbsp;   celestial\_score DECIMAL(5, 4),

&nbsp;   numerology\_score DECIMAL(5, 4),

&nbsp;   sentiment\_score DECIMAL(5, 4),

&nbsp;   political\_score DECIMAL(5, 4),

&nbsp;   -- Weights used for this calculation

&nbsp;   weights JSONB NOT NULL,               -- {"ta": 0.25, "onchain": 0.20, "celestial": 0.15, "numerology": 0.10, "sentiment": 0.15, "political": 0.15}

&nbsp;   -- Composite

&nbsp;   composite\_score DECIMAL(5, 4),        -- weighted sum, -1.0 to +1.0

&nbsp;   signal\_strength VARCHAR(10),          -- 'strong\_buy', 'buy', 'neutral', 'sell', 'strong\_sell'

&nbsp;   -- Which layers are aligned

&nbsp;   aligned\_layers JSONB,                 -- \["ta", "celestial", "numerology", "political"] — layers all pointing same direction

&nbsp;   alignment\_count INTEGER,              -- number of aligned layers

&nbsp;   PRIMARY KEY (timestamp, symbol, timeframe)

);



SELECT create\_hypertable('confluence\_scores', 'timestamp');

```



\### 4.9 Historical Events (for backtesting)



```sql

CREATE TABLE historical\_events (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   timestamp TIMESTAMPTZ NOT NULL,

&nbsp;   symbol VARCHAR(20) NOT NULL,

&nbsp;   event\_type VARCHAR(30) NOT NULL,      -- 'crash', 'pump', 'halving', 'ath', 'cycle\_low'

&nbsp;   magnitude\_pct DECIMAL(10, 4),         -- percentage move

&nbsp;   price\_at\_event DECIMAL(20, 8),

&nbsp;   duration\_hours INTEGER,               -- how long the move took

&nbsp;   -- Inter-event intervals (computed)

&nbsp;   days\_since\_previous\_crash INTEGER,

&nbsp;   days\_since\_previous\_pump INTEGER,

&nbsp;   days\_since\_previous\_halving INTEGER,

&nbsp;   -- Celestial state at time of event

&nbsp;   lunar\_phase\_name VARCHAR(20),

&nbsp;   mercury\_retrograde BOOLEAN,

&nbsp;   active\_aspects\_snapshot JSONB,

&nbsp;   -- Numerological state

&nbsp;   date\_universal\_number INTEGER,

&nbsp;   active\_cycle\_alignments JSONB,

&nbsp;   notes TEXT,

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE INDEX idx\_events\_type\_time ON historical\_events (event\_type, timestamp DESC);

CREATE INDEX idx\_events\_symbol ON historical\_events (symbol, timestamp DESC);

```



\### 4.9 Alerts



```sql

CREATE TABLE alerts (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW(),

&nbsp;   triggered\_at TIMESTAMPTZ,

&nbsp;   symbol VARCHAR(20) NOT NULL,

&nbsp;   alert\_type VARCHAR(30) NOT NULL,      -- 'confluence', 'cycle\_alignment', 'retrograde\_start', 'price\_level', 'custom'

&nbsp;   severity VARCHAR(10) NOT NULL,        -- 'info', 'warning', 'critical'

&nbsp;   title VARCHAR(200) NOT NULL,

&nbsp;   description TEXT,

&nbsp;   -- What triggered it

&nbsp;   trigger\_data JSONB,                   -- full context of what caused the alert

&nbsp;   composite\_score DECIMAL(5, 4),

&nbsp;   aligned\_layers JSONB,

&nbsp;   -- Status

&nbsp;   status VARCHAR(20) DEFAULT 'active',  -- 'active', 'acknowledged', 'dismissed'

&nbsp;   acknowledged\_at TIMESTAMPTZ

);

```



\### 4.10 User Configuration



```sql

CREATE TABLE signal\_weights (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   profile\_name VARCHAR(50) DEFAULT 'default',

&nbsp;   ta\_weight DECIMAL(5, 4) DEFAULT 0.25,

&nbsp;   onchain\_weight DECIMAL(5, 4) DEFAULT 0.20,

&nbsp;   celestial\_weight DECIMAL(5, 4) DEFAULT 0.15,

&nbsp;   numerology\_weight DECIMAL(5, 4) DEFAULT 0.10,

&nbsp;   sentiment\_weight DECIMAL(5, 4) DEFAULT 0.15,

&nbsp;   political\_weight DECIMAL(5, 4) DEFAULT 0.15,

&nbsp;   -- Weights must sum to 1.0

&nbsp;   is\_active BOOLEAN DEFAULT TRUE,

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW(),

&nbsp;   updated\_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE watched\_symbols (

&nbsp;   id SERIAL PRIMARY KEY,

&nbsp;   symbol VARCHAR(20) NOT NULL UNIQUE,   -- 'BTC/USDT', 'ETH/USDT', 'XRP/USDT'

&nbsp;   exchange VARCHAR(30) DEFAULT 'binance',

&nbsp;   is\_active BOOLEAN DEFAULT TRUE,

&nbsp;   timeframes JSONB DEFAULT '\["1h", "4h", "1d"]',

&nbsp;   created\_at TIMESTAMPTZ DEFAULT NOW()

);

```



---



\## 5. Signal Layer Specifications



\### 5.1 Layer 1 — Traditional Technical Analysis



\*\*Module:\*\* `signals/technical.py`



\*\*Inputs:\*\* Price data (OHLCV)



\*\*Indicators to compute:\*\*

\- RSI (7, 14 periods)

\- MACD (12, 26, 9)

\- Stochastic Oscillator (14, 3, 3)

\- Bollinger Bands (20, 2)

\- SMA (20, 50, 200)

\- EMA (12, 26)

\- ATR (14)

\- Fibonacci retracement levels (auto-detect swing high/low using zigzag or N-bar lookback)

\- Volume profile (relative volume vs 20-day average)



\*\*Score Computation (-1.0 to +1.0):\*\*

\- RSI > 70 = bearish signal (-0.5 to -1.0 scaled by how far above 70)

\- RSI < 30 = bullish signal (+0.5 to +1.0)

\- MACD crossover = +/- 0.3

\- Price below BB lower = bullish +0.3

\- Golden cross (50 SMA > 200 SMA) = +0.4

\- Death cross = -0.4

\- Price at Fibonacci level = +/- 0.2 (with direction based on trend)

\- Average all sub-signals with equal weight for composite ta\_score



\*\*Computation Frequency:\*\* Every new candle close (1h default, configurable)



\### 5.2 Layer 2 — On-Chain Analytics



\*\*Module:\*\* `signals/onchain.py`



\*\*Data Sources (pick one to start, expand later):\*\*

\- CryptoQuant API (free tier available)

\- Glassnode API

\- Santiment API



\*\*Metrics:\*\*

\- Exchange net flow (negative = bullish, coins leaving exchanges)

\- Whale transaction count (>$100k)

\- NUPL (Net Unrealized Profit/Loss) — above 0.75 = euphoria/bearish, below 0 = capitulation/bullish

\- MVRV Z-Score — above 7 = overvalued, below 0 = undervalued

\- SOPR — below 1 = selling at loss (capitulation)



\*\*Score Computation:\*\*

\- Each metric maps to a -1 to +1 range

\- Weighted average for composite onchain\_score

\- Default: equal weight across available metrics



\*\*Computation Frequency:\*\* Every 4 hours (on-chain data updates slowly)



\### 5.3 Layer 3 — Celestial / Esoteric Engine



\*\*Module:\*\* `signals/celestial.py`



\*\*Sub-module 3A — Astronomical Ephemeris:\*\*



\*\*Library:\*\* `pyswisseph` (Python bindings for Swiss Ephemeris)



\*\*Compute daily:\*\*

1\. \*\*Lunar phase\*\* — exact angle (0° = new moon, 180° = full moon)

2\. \*\*Planetary retrogrades\*\* — Mercury, Venus, Mars, Jupiter, Saturn

3\. \*\*Planetary longitudes\*\* — ecliptic longitude for each planet

4\. \*\*Aspects\*\* — conjunction (0°), sextile (60°), square (90°), trine (120°), opposition (180°) with configurable orb (default 8° for major aspects)

5\. \*\*Eclipse dates\*\* — flag lunar and solar eclipses

6\. \*\*Ingresses\*\* — when planets change zodiac signs



\*\*Astrological Score Rules (configurable, backtestable):\*\*

\- New moon: +0.2 (historically correlates with accumulation)

\- Full moon: -0.2 (historically correlates with distribution)

\- Mercury retrograde: -0.3 (increased volatility/reversals)

\- Saturn-Jupiter conjunction: +/- 0.4 (major cycle shifts)

\- Mars square Saturn: -0.3 (tension, conflict energy)

\- Eclipse within 3 days: -0.4 (high volatility expected)

\- Multiple retrogrades (3+): -0.5



\*\*Sub-module 3B — Numerological Engine:\*\*



\*\*Module:\*\* `signals/numerology.py`



\*\*Date Numerology:\*\*

```python

def universal\_day\_number(date):

&nbsp;   """

&nbsp;   Reduce a date to its universal day number.

&nbsp;   2026-02-20 -> 2+0+2+6+0+2+2+0 = 14 -> 1+4 = 5

&nbsp;   Preserve master numbers: 11, 22, 33

&nbsp;   """



def is\_master\_number\_date(date):

&nbsp;   """Check if date reduces to 11, 22, or 33"""



def date\_digit\_sum(date):

&nbsp;   """Raw digit sum before reduction"""

```



\*\*Custom Cycle Tracker:\*\*

```python

class CycleTracker:

&nbsp;   """

&nbsp;   Tracks N-day cycles from reference events.

&nbsp;   Primary use case: the 47-day crash cycle.



&nbsp;   Methods:

&nbsp;   - add\_cycle(name, days, reference\_date, reference\_event)

&nbsp;   - check\_date(date) -> list of active cycle alignments

&nbsp;   - days\_until\_next(cycle\_name) -> int

&nbsp;   - get\_hit\_rate(cycle\_name) -> float

&nbsp;   """

```



\*\*Gematria Calculator:\*\*

```python

class GematriaCalculator:

&nbsp;   """

&nbsp;   Multiple cipher support:

&nbsp;   - English Ordinal: A=1, B=2, ... Z=26

&nbsp;   - Full Reduction: A=1, B=2, ... I=9, J=1, K=2, ...

&nbsp;   - Reverse Ordinal: A=26, B=25, ... Z=1

&nbsp;   - Reverse Reduction: reduced reverse

&nbsp;   - Jewish/Hebrew Gematria

&nbsp;   - English Gematria (x6 multiplier)



&nbsp;   Methods:

&nbsp;   - calculate(text, cipher='english\_ordinal') -> int

&nbsp;   - calculate\_all\_ciphers(text) -> dict

&nbsp;   - find\_matches(target\_value, cipher) -> list of known terms

&nbsp;   - reduce\_to\_digit(number) -> int (with master number preservation)

&nbsp;   - analyze\_price\_level(price) -> dict of numerological properties

&nbsp;   """

```



\*\*Price-Number Analysis:\*\*

```python

def analyze\_price\_for\_significance(price, watched\_numbers=\[47, 11, 22, 33, 7, 9, 13]):

&nbsp;   """

&nbsp;   Check if a price level contains or relates to significant numbers.

&nbsp;   - Does the price contain '47'? (e.g., $47,000 or $104,700)

&nbsp;   - Does the price digit-sum to a significant number?

&nbsp;   - Is the price at a round number that reduces to a key digit?

&nbsp;   """

```



\*\*Numerology Score Rules:\*\*

\- Master number date (11, 22, 33): flag as high-energy day, +/- 0.2 based on other signals

\- 47-day cycle alignment: -0.4 (bearish based on observed pattern)

\- Multiple custom cycles aligning: multiply significance by overlap count

\- Price at gematria-significant level: +/- 0.1 as support/resistance signal

\- Universal day number matching gematria of active coin: +/- 0.15



\*\*Computation Frequency:\*\* Daily at 00:00 UTC, plus real-time price checks



\### 5.4 Layer 4 — Sentiment



\*\*Module:\*\* `signals/sentiment.py`



\*\*Data Sources:\*\*

\- Alternative.me Fear \& Greed Index API (free)

\- Optional: LunarCrush social metrics API

\- Optional: Google Trends via `pytrends`



\*\*Score Computation:\*\*

\- Fear \& Greed < 20 (Extreme Fear): +0.8 (contrarian bullish)

\- Fear \& Greed 20-40: +0.3

\- Fear \& Greed 40-60: 0.0 (neutral)

\- Fear \& Greed 60-80: -0.3

\- Fear \& Greed > 80 (Extreme Greed): -0.8 (contrarian bearish)



\*\*Computation Frequency:\*\* Every 4 hours



\### 5.5 Layer 5 — Political Events \& Macro Intelligence



\*\*Module:\*\* `signals/political.py`



\*\*Purpose:\*\* Track scheduled political/economic events and real-time news that move crypto markets. Political events are unique because they have both a \*pre-event\* signal (known events create anticipatory volatility) and a \*post-event\* signal (the actual outcome and market reaction).



\*\*Sub-module 5A — Political Calendar Engine:\*\*



\*\*Module:\*\* `signals/political\_calendar.py`



\*\*Data Sources:\*\*

\- Economic calendar APIs: Investing.com calendar, ForexFactory, TradingEconomics API

\- Government RSS feeds: whitehouse.gov, sec.gov, federalreserve.gov, congress.gov

\- Crypto-specific: SEC EDGAR (crypto-related filings), CFTC announcements

\- Manual entry for known upcoming events



\*\*Pre-Seeded Recurring Events:\*\*

```python

RECURRING\_POLITICAL\_EVENTS = \[

&nbsp;   {"type": "fomc\_meeting", "frequency": "8x/year", "volatility": "high", "category": "monetary\_policy"},

&nbsp;   {"type": "cpi\_release", "frequency": "monthly", "volatility": "high", "category": "monetary\_policy"},

&nbsp;   {"type": "jobs\_report", "frequency": "monthly", "volatility": "medium", "category": "fiscal\_policy"},

&nbsp;   {"type": "gdp\_release", "frequency": "quarterly", "volatility": "medium", "category": "fiscal\_policy"},

&nbsp;   {"type": "sec\_meeting", "frequency": "varies", "volatility": "high", "category": "crypto\_regulation"},

&nbsp;   {"type": "treasury\_refunding", "frequency": "quarterly", "volatility": "medium", "category": "monetary\_policy"},

&nbsp;   {"type": "opec\_meeting", "frequency": "~6x/year", "volatility": "medium", "category": "geopolitical"},

&nbsp;   {"type": "g7\_g20\_summit", "frequency": "annual", "volatility": "medium", "category": "geopolitical"},

&nbsp;   {"type": "us\_election", "frequency": "2yr/4yr", "volatility": "extreme", "category": "election"},

&nbsp;   {"type": "debt\_ceiling\_deadline", "frequency": "irregular", "volatility": "extreme", "category": "fiscal\_policy"},

]

```



\*\*Calendar Score Rules:\*\*

\- Major event within 24 hours: increase volatility expectation, score = 0.0 (direction unknown) but flag as "high volatility zone"

\- FOMC rate cut expected: +0.3 (liquidity bullish)

\- FOMC rate hike expected: -0.3 (liquidity bearish)

\- SEC crypto hearing scheduled: -0.2 (historically net bearish, regulatory uncertainty)

\- Tariff announcement: -0.3 (risk-off)

\- Election day within 7 days: flag "extreme uncertainty", widen alert thresholds

\- Debt ceiling crisis: -0.5 (extreme risk-off)

\- No major events within 7 days: +0.1 (calm macro = risk-on drift)



\*\*Sub-module 5B — Real-Time News Classifier:\*\*



\*\*Module:\*\* `signals/political\_news.py`



\*\*Data Sources (tiered by priority):\*\*

\- \*\*Tier 1 — Official Sources:\*\* Government press releases (SEC, Fed, White House). RSS feeds, scraped hourly.

\- \*\*Tier 2 — Wire Services:\*\* Reuters, AP, Bloomberg headlines. NewsAPI.org (free tier: 100 requests/day) or GNews API.

\- \*\*Tier 3 — Crypto News:\*\* CoinDesk, CoinTelegraph, The Block. RSS feeds or their APIs.

\- \*\*Tier 4 — Social Amplification:\*\* X/Twitter via API for mention velocity tracking of key political terms.



\*\*Classification Pipeline:\*\*

```python

class PoliticalNewsClassifier:

&nbsp;   """

&nbsp;   For each incoming news article:



&nbsp;   1. RELEVANCE FILTER

&nbsp;      - Quick keyword scan: does it mention crypto, bitcoin, SEC, Fed, tariff,

&nbsp;        regulation, sanctions, digital assets, CBDC, stablecoin, etc.?

&nbsp;      - If no keywords: discard (don't waste API calls)

&nbsp;      - If keywords: proceed to classification



&nbsp;   2. AI CLASSIFICATION (Claude API)

&nbsp;      - Send headline + first 500 chars to Claude with structured prompt:

&nbsp;        "Classify this news article for crypto market impact:

&nbsp;         - crypto\_relevance: 0.0-1.0

&nbsp;         - sentiment: -1.0 to +1.0 (bearish to bullish for crypto)

&nbsp;         - urgency: 0.0-1.0 (how time-sensitive)

&nbsp;         - category: \[monetary\_policy|crypto\_regulation|trade\_policy|geopolitical|election|fiscal\_policy]

&nbsp;         - subcategory: \[specific label]

&nbsp;         - entities: {people: \[], orgs: \[], countries: \[], coins: \[]}

&nbsp;         - expected\_impact\_duration: \[hours|days|weeks]

&nbsp;         Respond in JSON only."



&nbsp;   3. GEMATRIA ENRICHMENT

&nbsp;      - Run headline through GematriaCalculator

&nbsp;      - Run key entity names through GematriaCalculator

&nbsp;      - Store values for cross-reference with price levels



&nbsp;   4. AMPLIFICATION TRACKING (delayed, runs 1h and 4h after publish)

&nbsp;      - Count mentions of key terms from the article on social media

&nbsp;      - Track velocity: mentions/hour

&nbsp;      - High velocity + high relevance = stronger signal

&nbsp;      - Low velocity + high relevance = market hasn't priced it in yet (potential edge)



&nbsp;   5. IMPACT TRACKING (delayed, runs 1h, 4h, 24h after publish)

&nbsp;      - Record BTC price at each interval

&nbsp;      - Calculate actual impact percentage

&nbsp;      - Feed back into scoring model to improve future predictions

&nbsp;   """

```



\*\*News Score Computation:\*\*

```python

def compute\_political\_news\_score(recent\_articles, hours\_window=24):

&nbsp;   """

&nbsp;   Aggregate recent political news into a single score.



&nbsp;   1. Filter to articles with crypto\_relevance > 0.3

&nbsp;   2. Weight each article: sentiment \* relevance \* urgency \* recency\_decay

&nbsp;      - recency\_decay: exponential decay, half-life = 6 hours

&nbsp;   3. Take weighted average of all articles

&nbsp;   4. Amplification multiplier: if mention\_velocity > threshold, amplify by 1.5x

&nbsp;   5. Clamp to -1.0 to +1.0

&nbsp;   """

```



\*\*Sub-module 5C — Narrative Detector:\*\*



\*\*Module:\*\* `signals/political\_narrative.py`



```python

class NarrativeDetector:

&nbsp;   """

&nbsp;   Identifies dominant political/macro narratives that persist over days/weeks.

&nbsp;   These are more important than individual news events because narratives

&nbsp;   drive sustained positioning.



&nbsp;   Known narrative patterns:

&nbsp;   - 'rate\_cut\_expectations': Fed dovish signals accumulating -> bullish crypto

&nbsp;   - 'regulatory\_crackdown': SEC enforcement actions clustering -> bearish

&nbsp;   - 'etf\_momentum': ETF approvals/filings -> bullish

&nbsp;   - 'trade\_war\_escalation': tariff announcements -> bearish risk-off

&nbsp;   - 'defi\_regulation': specific DeFi targeting -> bearish for DeFi, may be neutral BTC

&nbsp;   - 'cbdc\_progress': government digital currency news -> mixed, watch for 'ban private crypto' subnarrative

&nbsp;   - 'bipartisan\_crypto\_support': legislation with bipartisan backing -> bullish

&nbsp;   - 'stablecoin\_regulation': clarity on stablecoins -> generally bullish (legitimizing)

&nbsp;   - 'mining\_restrictions': energy/environmental focus -> bearish for mining, muted on BTC price

&nbsp;   - 'sovereign\_adoption': countries adding BTC to reserves -> strongly bullish



&nbsp;   Process:

&nbsp;   1. Every 4 hours, analyze last 72 hours of classified news

&nbsp;   2. Cluster articles by category + subcategory

&nbsp;   3. If a cluster has 5+ articles with consistent direction -> active narrative

&nbsp;   4. Assign narrative\_strength (based on article count + avg relevance)

&nbsp;   5. Assign narrative\_direction (based on avg sentiment of cluster)

&nbsp;   6. Track narrative persistence: how many consecutive 4h windows has this narrative been active?

&nbsp;   7. Longer persistence = stronger signal weight

&nbsp;   """

```



\*\*Composite Political Score:\*\*

```python

def compute\_political\_score():

&nbsp;   """

&nbsp;   Combines all sub-modules:



&nbsp;   political\_score = (

&nbsp;       0.30 \* calendar\_proximity\_score +    # scheduled event impact

&nbsp;       0.35 \* news\_sentiment\_score +         # real-time news flow

&nbsp;       0.35 \* narrative\_score                # persistent narrative direction

&nbsp;   )



&nbsp;   Special overrides:

&nbsp;   - If a "black swan" news item detected (urgency > 0.9, relevance > 0.9):

&nbsp;     override composite, set political\_score = article sentiment \* 0.8

&nbsp;   - If FOMC day: boost calendar\_proximity\_score weight to 0.50

&nbsp;   """

```



\*\*Computation Frequency:\*\*

\- Calendar events: checked daily, countdowns updated hourly

\- News classification: every 15-30 minutes (batch incoming articles)

\- Narrative detection: every 4 hours

\- Composite political\_score: hourly



---



\## 6. Confluence Scoring Engine



\*\*Module:\*\* `engine/confluence.py`



\### 6.1 Score Computation



```python

class ConfluenceEngine:

&nbsp;   def compute\_score(self, symbol, timestamp, weights=None):

&nbsp;       """

&nbsp;       1. Gather latest scores from each layer (TA, on-chain, celestial, numerology, sentiment, political)

&nbsp;       2. Apply weights (from signal\_weights table or override)

&nbsp;       3. Compute weighted average

&nbsp;       4. Determine signal\_strength label

&nbsp;       5. Identify aligned layers (all pointing same direction)

&nbsp;       6. Store result in confluence\_scores table

&nbsp;       """



&nbsp;   def get\_alignment(self, scores: dict) -> dict:

&nbsp;       """

&nbsp;       Determine which layers agree.

&nbsp;       If ta\_score > 0.2 AND celestial\_score > 0.2 AND political\_score > 0.2,

&nbsp;       those three are 'aligned bullish'.

&nbsp;       High alignment count = higher conviction signal.

&nbsp;       Max possible alignment: 6/6 layers.

&nbsp;       """

```



\### 6.2 Signal Strength Thresholds



| Composite Score | Label | Action Suggestion |

|----------------|-------|-------------------|

| +0.6 to +1.0 | `strong\_buy` | High confluence bullish |

| +0.2 to +0.6 | `buy` | Moderate bullish |

| -0.2 to +0.2 | `neutral` | No clear signal |

| -0.6 to -0.2 | `sell` | Moderate bearish |

| -1.0 to -0.6 | `strong\_sell` | High confluence bearish |



\### 6.3 Alert Triggers



Generate an alert when:

1\. \*\*Confluence threshold crossed:\*\* composite\_score moves above +0.5 or below -0.5

2\. \*\*Layer alignment:\*\* 4+ layers agree on direction (now out of 6 total)

3\. \*\*Cycle alignment:\*\* A tracked custom cycle (e.g., 47-day) reaches its target date (+/- tolerance)

4\. \*\*Celestial event:\*\* Mercury retrograde starts/ends, eclipse within 48 hours

5\. \*\*Extreme sentiment:\*\* Fear \& Greed < 10 or > 90

6\. \*\*Numerological date:\*\* Master number date + other aligned signals

7\. \*\*Political black swan:\*\* News article with urgency > 0.9 AND relevance > 0.9

8\. \*\*Major scheduled event:\*\* High-impact political calendar event within 24 hours

9\. \*\*Narrative shift:\*\* Dominant narrative changes direction (bullish -> bearish or vice versa)

10\. \*\*Esoteric-political confluence:\*\* Major political event date has significant gematria value AND aligns with a custom cycle



---



\## 7. Backtesting Module



\*\*Module:\*\* `engine/backtester.py`



\### 7.1 The 47-Day Cycle Backtester (Priority #1)



```python

class CycleBacktester:

&nbsp;   """

&nbsp;   Purpose: Validate the 47-day (and other) crash cycle hypothesis.



&nbsp;   Process:

&nbsp;   1. Pull all BTC daily price data going back to 2015

&nbsp;   2. Identify all significant drops (configurable: >8%, >10%, >15% within 48-72 hours)

&nbsp;   3. Calculate day-count intervals between every pair of consecutive drops

&nbsp;   4. Statistical analysis:

&nbsp;      a. Frequency distribution of all intervals

&nbsp;      b. Highlight intervals that are multiples of 47 or within +/-2 of 47

&nbsp;      c. Chi-squared test: are 47-day intervals more frequent than expected by chance?

&nbsp;      d. Cross-reference with celestial state at each crash

&nbsp;      e. Cross-reference with numerological properties of each crash date

&nbsp;   5. Output: report with confidence score for the 47-day hypothesis

&nbsp;   """

```



\### 7.2 General Signal Backtester



```python

class SignalBacktester:

&nbsp;   """

&nbsp;   For any signal layer or combination:

&nbsp;   1. Replay historical data day by day

&nbsp;   2. Compute what each layer's score would have been

&nbsp;   3. Track: if you acted on signals above threshold X, what would your P\&L be?

&nbsp;   4. Optimize weights: which weight combination maximizes hit rate?



&nbsp;   Output: hit\_rate, avg\_return\_on\_signal, max\_drawdown, sharpe\_ratio\_equivalent

&nbsp;   """

```



---



\## 8. API Endpoints



\### 8.1 Market Data

```

GET  /api/v1/price/{symbol}                    # Current price + recent candles

GET  /api/v1/price/{symbol}/history             # Historical OHLCV

WS   /ws/price/{symbol}                         # Real-time price stream

```



\### 8.2 Signals

```

GET  /api/v1/signals/{symbol}                   # Current scores for all layers

GET  /api/v1/signals/{symbol}/history           # Historical signal scores

GET  /api/v1/signals/{symbol}/ta                # TA indicators detail

GET  /api/v1/signals/{symbol}/celestial         # Current celestial state

GET  /api/v1/signals/{symbol}/numerology        # Current numerological state

GET  /api/v1/signals/{symbol}/political         # Current political signal state

```



\### 8.3 Confluence

```

GET  /api/v1/confluence/{symbol}                # Current composite score

GET  /api/v1/confluence/{symbol}/history        # Historical composite scores

POST /api/v1/confluence/weights                 # Update signal weights

GET  /api/v1/confluence/weights                 # Get current weights

```



\### 8.4 Cycles \& Gematria

```

GET  /api/v1/cycles                             # List all tracked cycles

POST /api/v1/cycles                             # Add a new cycle to track

GET  /api/v1/cycles/{id}/status                 # Current cycle day + next target date

GET  /api/v1/gematria/calculate                 # Calculate gematria for a term

GET  /api/v1/gematria/lookup/{value}            # Find terms matching a gematria value

GET  /api/v1/calendar                           # Upcoming celestial + numerological + political events

```



\### 8.5 Political Events

```

GET  /api/v1/political/calendar                 # Upcoming scheduled political events

POST /api/v1/political/calendar                 # Manually add a political event

GET  /api/v1/political/news                     # Recent classified political news

GET  /api/v1/political/news/feed                # Raw news feed with classification

GET  /api/v1/political/narrative                # Current dominant narrative(s)

GET  /api/v1/political/narrative/history         # Narrative shifts over time

GET  /api/v1/political/score                    # Current composite political score

GET  /api/v1/political/gematria/{event\_id}       # Gematria analysis of a specific event

WS   /ws/political/breaking                      # Real-time breaking political news stream

```



\### 8.6 Backtesting

```

POST /api/v1/backtest/cycle                     # Run cycle backtester

POST /api/v1/backtest/signals                   # Run signal backtester

GET  /api/v1/backtest/results/{id}              # Get backtest results

```



\### 8.6 Alerts

```

GET  /api/v1/alerts                             # List active alerts

POST /api/v1/alerts/{id}/acknowledge            # Acknowledge an alert

WS   /ws/alerts                                 # Real-time alert stream

```



---



\## 9. Frontend Dashboard



\### 9.1 Main Dashboard View



```

┌─────────────────────────────────────────────────────────────┐

│  CryptoOracle                                    BTC/USDT   │

├─────────────────────────────────────┬───────────────────────┤

│                                     │  CONFLUENCE SCORE     │

│   Price Chart (TradingView-style)   │  ████████░░  +0.62   │

│   with TA overlay toggles           │  STRONG BUY           │

│   (RSI, BB, Fib, MA)               │                       │

│                                     │  Layer Breakdown:     │

│                                     │  TA:        +0.45 ██  │

│                                     │  On-Chain:  +0.70 ███ │

│                                     │  Celestial: +0.55 ██  │

│                                     │  Numerology:+0.80 ████│

│                                     │  Sentiment: +0.60 ███ │

│                                     │  Political: +0.35 ██  │

│                                     │                       │

│                                     │  Aligned: 6/6 ✓       │

├─────────────────────────────────────┼───────────────────────┤

│  ACTIVE ALERTS                      │  CELESTIAL STATE      │

│  🔴 47-Day Cycle: Day 43/47        │  Moon: Waxing Gibbous │

│  🟡 Mercury Retrograde in 5 days   │  ☿ Retrograde: No    │

│  🟢 F\&G Index: 22 (Extreme Fear)   │  Active Aspects:      │

│  🟠 FOMC Meeting in 2 days         │  ♂ □ ♄ (Mars sq Sat) │

│  🔵 Narrative: Rate Cut Momentum   │  Date: Universal #5   │

├─────────────────────────────────────┴───────────────────────┤

│  CYCLE TRACKER                                              │

│  ┌──────────────┬────────┬───────────┬──────────┬─────────┐ │

│  │ Cycle        │ Day    │ Next Hit  │ Hit Rate │ Status  │ │

│  │ 47-Day Crash │ 43/47  │ Feb 24    │ 72%      │ ⚠ NEAR │ │

│  │ Lunar Cycle  │ 12/29  │ Mar 03    │ 58%      │ Normal  │ │

│  │ 33-Day Rev.  │ 8/33   │ Mar 15    │ 45%      │ Normal  │ │

│  └──────────────┴────────┴───────────┴──────────┴─────────┘ │

└─────────────────────────────────────────────────────────────┘

```



\### 9.2 Additional Views



\- \*\*Cycle Calendar:\*\* Monthly calendar view showing upcoming cycle dates, celestial events, master number dates, eclipse dates

\- \*\*Backtest Results:\*\* Charts showing cycle hit rates, signal accuracy over time

\- \*\*Gematria Tool:\*\* Interactive calculator — enter a term, see all cipher values, find matching terms/prices

\- \*\*Weight Tuner:\*\* Slider interface to adjust layer weights, with live backtest preview

\- \*\*Historical Events Map:\*\* Timeline of crashes/pumps with celestial + numerological state overlaid



---



\## 10. MVP Build Phases



\### Phase 1 — Foundation (Week 1-2)

\*\*Goal:\*\* Data pipeline running, basic TA signals, database populated



\- \[ ] Project scaffolding: FastAPI app, Docker Compose (Postgres+TimescaleDB, Redis)

\- \[ ] Database migrations (all tables from Section 4)

\- \[ ] CCXT integration: fetch and store BTC/USDT, ETH/USDT, XRP/USDT historical daily data from Binance (at least back to 2017)

\- \[ ] TA indicator computation module using `pandas-ta`

\- \[ ] Basic scheduler: fetch new candles every hour, compute TA indicators

\- \[ ] Seed `historical\_events` table with known BTC crashes (>10% drops) — manually curate from price data



\### Phase 2 — Esoteric Engines (Week 3-4)

\*\*Goal:\*\* Celestial and numerology layers operational



\- \[ ] Swiss Ephemeris integration (`pyswisseph`)

\- \[ ] Daily celestial state computation: lunar phase, retrogrades, aspects, eclipses

\- \[ ] Backfill celestial\_state table for all historical dates (2015-present)

\- \[ ] Gematria calculator module with multiple ciphers

\- \[ ] Numerology daily computation: universal day numbers, master number flags

\- \[ ] Custom cycle tracker: implement 47-day cycle + ability to add more

\- \[ ] Backfill numerology\_daily table

\- \[ ] Cross-reference historical\_events with celestial + numerological state



\### Phase 3 — Confluence \& Backtesting (Week 5-6)

\*\*Goal:\*\* All layers scoring, backtester validating



\- \[ ] Sentiment module: Fear \& Greed Index API integration

\- \[ ] On-chain module: CryptoQuant or Glassnode free tier integration

\- \[ ] Confluence scoring engine: weighted composite + alignment detection (6 layers)

\- \[ ] 47-Day Cycle Backtester: statistical validation with full report output

\- \[ ] General signal backtester: replay historical data, compute hypothetical signals

\- \[ ] Weight optimization: brute-force or grid search for optimal layer weights

\- \[ ] Alert engine: threshold-based alert generation + storage



\### Phase 4 — Political Events Layer (Week 7-8)

\*\*Goal:\*\* Political intelligence fully integrated as Layer 5



\- \[ ] Political calendar engine: seed with recurring events (FOMC, CPI, etc.)

\- \[ ] Government RSS feed integration (SEC, Fed, White House, Congress)

\- \[ ] NewsAPI or GNews integration for real-time headline ingestion

\- \[ ] Claude API classification pipeline: relevance, sentiment, urgency scoring

\- \[ ] Gematria enrichment of political events (headline + key figure analysis)

\- \[ ] Amplification tracking: social mention velocity after major news

\- \[ ] Impact tracking: record BTC price at 1h/4h/24h after political news

\- \[ ] Narrative detector: cluster analysis of recent political news

\- \[ ] Composite political\_score computation

\- \[ ] Backfill: classify major historical political events (2020-present) and correlate with price action

\- \[ ] Add political\_score to confluence engine



\### Phase 5 — Frontend Dashboard (Week 9-10)

\*\*Goal:\*\* Usable dashboard with real-time updates



\- \[ ] React app scaffolding with Tailwind CSS

\- \[ ] Main dashboard: price chart, confluence score gauge, layer breakdown (6 layers)

\- \[ ] Celestial state panel with current moon phase, retrogrades, aspects

\- \[ ] Political intelligence panel: upcoming events, current narrative, breaking news feed

\- \[ ] Cycle tracker table with countdown to next alignment dates

\- \[ ] Alert feed with real-time WebSocket updates

\- \[ ] Cycle calendar view (monthly) — merged celestial + political + numerological events

\- \[ ] Gematria calculator interactive tool

\- \[ ] Weight tuner with sliders (6 layer weights)

\- \[ ] Backtest results visualization



\### Phase 6 — Polish \& Extend (Week 11-12)

\*\*Goal:\*\* Refined, reliable, expandable



\- \[ ] Historical event timeline with overlaid celestial/numerological/political state

\- \[ ] Political event impact scorecard: compare expected vs actual impact over time

\- \[ ] Additional symbols support (easy add via watched\_symbols)

\- \[ ] Email/SMS/push alert notifications

\- \[ ] Multiple weight profiles (aggressive, conservative, esoteric-heavy, macro-heavy)

\- \[ ] Export data to CSV

\- \[ ] Documentation and README



---



\## 11. MVP Configuration Defaults



```json

{

&nbsp; "watched\_symbols": \["BTC/USDT", "ETH/USDT", "XRP/USDT"],

&nbsp; "default\_exchange": "binance",

&nbsp; "default\_timeframes": \["1h", "4h", "1d"],

&nbsp; "signal\_weights": {

&nbsp;   "ta": 0.25,

&nbsp;   "onchain": 0.20,

&nbsp;   "celestial": 0.15,

&nbsp;   "numerology": 0.10,

&nbsp;   "sentiment": 0.15,

&nbsp;   "political": 0.15

&nbsp; },

&nbsp; "alert\_thresholds": {

&nbsp;   "confluence\_high": 0.5,

&nbsp;   "confluence\_low": -0.5,

&nbsp;   "min\_aligned\_layers": 4,

&nbsp;   "cycle\_proximity\_days": 3

&nbsp; },

&nbsp; "custom\_cycles": \[

&nbsp;   {

&nbsp;     "name": "47-Day Crash Cycle",

&nbsp;     "days": 47,

&nbsp;     "tolerance": 2,

&nbsp;     "direction": "bearish"

&nbsp;   }

&nbsp; ],

&nbsp; "watched\_numbers": \[7, 9, 11, 13, 22, 33, 47],

&nbsp; "aspect\_orb\_degrees": 8,

&nbsp; "ta\_indicators": {

&nbsp;   "rsi\_periods": \[7, 14],

&nbsp;   "macd": \[12, 26, 9],

&nbsp;   "bb\_period": 20,

&nbsp;   "bb\_std": 2,

&nbsp;   "sma\_periods": \[20, 50, 200],

&nbsp;   "ema\_periods": \[12, 26],

&nbsp;   "atr\_period": 14

&nbsp; }

}

```



---



\## 12. Key Dependencies



```

\# requirements.txt

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

\# package.json (frontend)

{

&nbsp; "dependencies": {

&nbsp;   "react": "^18",

&nbsp;   "recharts": "^2.10",

&nbsp;   "tailwindcss": "^3.4",

&nbsp;   "lightweight-charts": "^4.1",   // TradingView charts

&nbsp;   "axios": "^1.6",

&nbsp;   "socket.io-client": "^4.7"

&nbsp; }

}

```



---



\## 13. Environment Variables



```env

\# .env

DATABASE\_URL=postgresql://user:pass@localhost:5432/cryptooracle

REDIS\_URL=redis://localhost:6379

EXCHANGE\_API\_KEY=              # Optional: for higher rate limits

EXCHANGE\_API\_SECRET=

CRYPTOQUANT\_API\_KEY=           # On-chain data

ALTERNATIVE\_ME\_API=            # Fear \& Greed (free, no key needed)

LUNARCRUSH\_API\_KEY=            # Optional: social sentiment

NEWSAPI\_KEY=                   # NewsAPI.org for headline ingestion

ANTHROPIC\_API\_KEY=             # Claude API for news classification + gematria analysis

GNEWS\_API\_KEY=                 # Optional: GNews as backup news source

ALERT\_EMAIL=                   # Optional: email notifications

```



---



\## 14. Notes for Claude Code



\- \*\*Start with Phase 1.\*\* Get the data pipeline and database working first. Everything else depends on good historical data.

\- \*\*The 47-day cycle backtester is the highest-priority unique feature.\*\* Prioritize getting enough historical crash data to validate or invalidate this pattern with statistical rigor.

\- \*\*Swiss Ephemeris requires the ephemeris data files.\*\* Download the Swiss Ephemeris data files (freely available) and include them in the Docker image or mount them as a volume.

\- \*\*All scores use -1.0 to +1.0 range.\*\* This normalization is critical for the confluence engine to work properly across heterogeneous signal types.

\- \*\*Every scoring rule should be configurable via the database or config file.\*\* The user will want to tune rules like "Mercury retrograde = -0.3" based on backtest results.

\- \*\*Build the gematria calculator as a standalone module\*\* that can be imported and used independently — it's useful outside the trading context too.

\- \*\*The political layer uses Claude's API for classification.\*\* Keep API calls efficient — batch articles when possible, use short structured prompts that request JSON output only. Cache classification results so you never re-classify the same headline.

\- \*\*Political calendar events should be pre-seeded.\*\* On first run, populate the political\_calendar table with known 2026 FOMC dates, CPI release dates, and other scheduled macro events. These are available from the Fed's website and economic calendar sites.

\- \*\*RSS feeds are the cheapest news source.\*\* Start with government RSS feeds (sec.gov, federalreserve.gov) and crypto news RSS (CoinDesk, CoinTelegraph) before paying for NewsAPI. Most news sites publish RSS feeds that can be parsed with `feedparser`.

\- \*\*The narrative detector is high value but can be Phase 4.\*\* Individual news classification is more important in MVP; narrative detection adds the persistent trend layer that makes the political signal much more powerful over time.

\- \*\*Gematria enrichment of political events is a unique cross-layer feature.\*\* When a political event's date, title, or key figure's name carries gematria significance that aligns with the numerology layer, flag it as a compound signal. This is something no other trading platform does.

\- \*\*The frontend is Phase 5 for a reason.\*\* The backend intelligence is what matters. A beautiful dashboard with bad signals is useless. Get the signals right first.

\- \*\*Use Alembic for database migrations\*\* from the start. Schema will evolve.

\- \*\*Log everything.\*\* Every signal computation, every alert trigger, every API call, every news classification. You'll need this for debugging and backtesting validation.

\- \*\*Impact tracking is what makes the political layer self-improving.\*\* By recording BTC price at 1h/4h/24h after each classified article, you build a training set that reveals which types of political events actually move crypto and which are noise. Over time, this feedback loop makes the political\_score increasingly accurate.



---



\*This PRD is designed to be consumed by Claude Code for iterative development. Each phase can be built, tested, and validated independently before moving to the next.\*

