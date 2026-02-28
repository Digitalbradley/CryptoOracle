"""XRP Adoption Intelligence (XAI) models — Phase A.

Tables: xai_onchain_metrics, xai_composite, xai_partnerships,
        xai_tracked_entities, xai_event_calendar.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DECIMAL,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ---------- On-chain utility metrics (daily) ----------

class XaiOnchainMetrics(Base):
    """Daily XRPL ledger metrics + RLUSD data + utility/speculation ratio."""

    __tablename__ = "xai_onchain_metrics"

    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    # Volume metrics
    xrpl_tx_count: Mapped[int | None] = mapped_column(BigInteger)
    xrpl_payment_volume_usd: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))
    xrpl_dex_volume_usd: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))

    # RLUSD metrics
    rlusd_total_supply: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))
    rlusd_unique_holders: Mapped[int | None] = mapped_column(Integer)
    rlusd_trust_line_count: Mapped[int | None] = mapped_column(Integer)

    # Utility vs speculation
    utility_volume_usd: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))
    speculation_volume_usd: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))
    utility_to_speculation_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6))

    # Network metrics
    xrpl_active_addresses: Mapped[int | None] = mapped_column(Integer)
    xrpl_new_accounts: Mapped[int | None] = mapped_column(Integer)

    # Exchange reserve
    xrp_exchange_reserve: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))

    __table_args__ = (
        Index("idx_xai_onchain_ts", "timestamp"),
    )


# ---------- Composite XAI scores ----------

class XaiComposite(Base):
    """Computed XAI composite score per run."""

    __tablename__ = "xai_composite"

    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    # Sub-signals (each -1.0 to +1.0)
    policy_pipeline_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    partnership_deployment_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    onchain_utility_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    personnel_intelligence_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    # Composite
    xai_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))

    # Key derived metrics
    utility_to_speculation_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6))
    rlusd_market_cap: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))
    active_partnership_count: Mapped[int | None] = mapped_column(Integer)
    partnerships_in_production: Mapped[int | None] = mapped_column(Integer)

    # Regime / phase
    adoption_phase: Mapped[str | None] = mapped_column(String(30))

    # Weights used
    weights: Mapped[dict | None] = mapped_column(JSON)

    __table_args__ = (
        Index("idx_xai_composite_ts", "timestamp"),
    )


# ---------- Partnership pipeline ----------

class XaiPartnership(Base):
    """Ripple institutional partnership pipeline tracking."""

    __tablename__ = "xai_partnerships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_name: Mapped[str] = mapped_column(String(200), nullable=False)
    partner_type: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str | None] = mapped_column(String(50))
    is_cpmi_member_country: Mapped[bool] = mapped_column(Boolean, default=False)
    partnership_type: Mapped[str | None] = mapped_column(String(50))

    pipeline_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    stage_score: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 2))
    partner_weight: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 1))

    announced_date: Mapped[date | None] = mapped_column(Date)
    stage_updated_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ---------- Tracked entities (people / institutions) ----------

class XaiTrackedEntity(Base):
    """Key individuals and institutions tracked for XRP adoption intelligence."""

    __tablename__ = "xai_tracked_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str | None] = mapped_column(String(300))
    institution: Mapped[str | None] = mapped_column(String(200))
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(50))
    cpmi_member: Mapped[bool] = mapped_column(Boolean, default=False)
    fsb_member: Mapped[bool] = mapped_column(Boolean, default=False)

    watch_urls: Mapped[dict | None] = mapped_column(JSON)
    social_handles: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(default=datetime.utcnow)


# ---------- Institutional event calendar ----------

class XaiEventCalendar(Base):
    """Upcoming XRP-relevant institutional events."""

    __tablename__ = "xai_event_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_name: Mapped[str] = mapped_column(String(300), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    xrp_relevance: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 2))
    potential_impact: Mapped[str | None] = mapped_column(String(20))
    recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_pattern: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(default=datetime.utcnow)
