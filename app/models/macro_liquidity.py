"""Macro liquidity raw data + composite signal models (Layer 7).

Tables: liquidity_data, rate_data, macro_prices, carry_trade_data,
        oil_data, macro_liquidity_signal.

Schema matches CryptoOracle_MVP_PRD Layer 7 brief Section 6.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ---------- Fed liquidity / balance sheet (FRED) ----------

class LiquidityData(Base):
    """Fed balance sheet, M2, reserves, RRP — from FRED."""

    __tablename__ = "liquidity_data"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    m2_supply: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))
    fed_balance_sheet: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))
    fed_funds_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    treasury_general_acct: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))
    reverse_repo: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))
    net_liquidity: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))

    __table_args__ = (
        Index("idx_liquidity_ts", "timestamp"),
    )


# ---------- Treasury yields / rates (FRED) ----------

class RateData(Base):
    """Treasury yields, breakevens, real rates — from FRED."""

    __tablename__ = "rate_data"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    dgs2: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    dgs10: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    yield_curve_2s10s: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    dfii10: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    t5yie: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    cpi_yoy: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))

    __table_args__ = (
        Index("idx_rate_ts", "timestamp"),
    )


# ---------- Dollar index + VIX (FRED) ----------

class MacroPrices(Base):
    """Dollar index (trade-weighted) and VIX — from FRED."""

    __tablename__ = "macro_prices"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    dxy_index: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    vix: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))

    __table_args__ = (
        Index("idx_macroprices_ts", "timestamp"),
    )


# ---------- Carry trade / forex (Twelve Data + CFTC) ----------

class CarryTradeData(Base):
    """Forex pairs, CFTC positioning, carry stress metrics."""

    __tablename__ = "carry_trade_data"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    usdjpy: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 6))
    eurusd: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 6))
    usdjpy_sma_20: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 6))
    usdjpy_atr_14: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 6))
    usdjpy_rsi_14: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))

    jpy_net_positioning: Mapped[int | None] = mapped_column(Integer)
    jpy_positioning_zscore: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))

    carry_stress_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    __table_args__ = (
        Index("idx_carry_ts", "timestamp"),
    )


# ---------- Oil prices + inventory (FRED + EIA) ----------

class OilData(Base):
    """Crude oil prices and EIA inventory data."""

    __tablename__ = "oil_data"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    wti_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    brent_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    wti_brent_spread: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    crude_inventory: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))
    inventory_change: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))

    __table_args__ = (
        Index("idx_oil_ts", "timestamp"),
    )


# ---------- Computed composite signal ----------

class MacroLiquiditySignal(Base):
    """Computed macro liquidity composite signal — stored per run."""

    __tablename__ = "macro_liquidity_signal"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    # Sub-signal scores (each -1.0 to +1.0)
    liquidity_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    treasury_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    dollar_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    oil_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    carry_trade_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    # Composite
    macro_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    # Regime classification
    regime: Mapped[str | None] = mapped_column(String(30))
    regime_confidence: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    # Key data points snapshot (for display without extra queries)
    net_liquidity: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))
    m2_yoy_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    yield_curve_2s10s: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    dxy_value: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    vix_value: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    wti_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4))
    usdjpy_value: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 6))
    carry_stress: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    # Sub-signal detail JSON for frontend
    sub_signals: Mapped[dict | None] = mapped_column(JSON)

    __table_args__ = (
        Index("idx_macro_signal_ts", "timestamp"),
    )
