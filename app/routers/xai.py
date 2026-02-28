"""XAI (XRP Adoption Intelligence) router — on-chain metrics, partnerships, events."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.xai import (
    XaiComposite,
    XaiEventCalendar,
    XaiOnchainMetrics,
    XaiPartnership,
)

router = APIRouter(tags=["xai"])


@router.get("/api/xai/score")
def get_xai_score(db: Session = Depends(get_db)):
    """Get latest XAI composite score with sub-signals and adoption phase."""
    row = db.execute(
        select(XaiComposite)
        .order_by(XaiComposite.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not row:
        return {"status": "no_data"}

    return {
        "timestamp": row.timestamp.isoformat(),
        "xai_score": str(row.xai_score),
        "policy_pipeline_score": str(row.policy_pipeline_score) if row.policy_pipeline_score else None,
        "partnership_deployment_score": str(row.partnership_deployment_score) if row.partnership_deployment_score else None,
        "onchain_utility_score": str(row.onchain_utility_score) if row.onchain_utility_score else None,
        "personnel_intelligence_score": str(row.personnel_intelligence_score) if row.personnel_intelligence_score else None,
        "utility_to_speculation_ratio": str(row.utility_to_speculation_ratio) if row.utility_to_speculation_ratio else None,
        "rlusd_market_cap": str(row.rlusd_market_cap) if row.rlusd_market_cap else None,
        "active_partnership_count": row.active_partnership_count,
        "partnerships_in_production": row.partnerships_in_production,
        "adoption_phase": row.adoption_phase,
        "weights": row.weights,
    }


@router.get("/api/xai/onchain")
def get_xai_onchain(db: Session = Depends(get_db)):
    """Get latest XRPL on-chain metrics."""
    row = db.execute(
        select(XaiOnchainMetrics)
        .order_by(XaiOnchainMetrics.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not row:
        return {"status": "no_data"}

    return {
        "timestamp": row.timestamp.isoformat(),
        "xrpl_tx_count": row.xrpl_tx_count,
        "xrpl_payment_volume_usd": str(row.xrpl_payment_volume_usd) if row.xrpl_payment_volume_usd else None,
        "xrpl_dex_volume_usd": str(row.xrpl_dex_volume_usd) if row.xrpl_dex_volume_usd else None,
        "rlusd_total_supply": str(row.rlusd_total_supply) if row.rlusd_total_supply else None,
        "rlusd_unique_holders": row.rlusd_unique_holders,
        "rlusd_trust_line_count": row.rlusd_trust_line_count,
        "utility_volume_usd": str(row.utility_volume_usd) if row.utility_volume_usd else None,
        "speculation_volume_usd": str(row.speculation_volume_usd) if row.speculation_volume_usd else None,
        "utility_to_speculation_ratio": str(row.utility_to_speculation_ratio) if row.utility_to_speculation_ratio else None,
        "xrpl_active_addresses": row.xrpl_active_addresses,
        "xrpl_new_accounts": row.xrpl_new_accounts,
        "xrp_exchange_reserve": str(row.xrp_exchange_reserve) if row.xrp_exchange_reserve else None,
    }


@router.get("/api/xai/partnerships")
def get_xai_partnerships(db: Session = Depends(get_db)):
    """Get all tracked Ripple partnerships with pipeline stages."""
    rows = db.execute(
        select(XaiPartnership).order_by(XaiPartnership.partner_weight.desc())
    ).scalars().all()

    partnerships = []
    for p in rows:
        partnerships.append({
            "id": p.id,
            "partner_name": p.partner_name,
            "partner_type": p.partner_type,
            "country": p.country,
            "is_cpmi_member_country": p.is_cpmi_member_country,
            "partnership_type": p.partnership_type,
            "pipeline_stage": p.pipeline_stage,
            "stage_score": str(p.stage_score) if p.stage_score else None,
            "partner_weight": str(p.partner_weight) if p.partner_weight else None,
            "announced_date": p.announced_date.isoformat() if p.announced_date else None,
            "notes": p.notes,
        })

    # Pipeline summary
    stages = {"announced": 0, "pilot": 0, "production": 0}
    for p in rows:
        if p.pipeline_stage in stages:
            stages[p.pipeline_stage] += 1

    return {
        "count": len(partnerships),
        "pipeline_summary": stages,
        "partnerships": partnerships,
    }


@router.get("/api/xai/calendar")
def get_xai_calendar(db: Session = Depends(get_db)):
    """Get upcoming XRP-relevant institutional events."""
    today = date.today()
    rows = db.execute(
        select(XaiEventCalendar)
        .where(XaiEventCalendar.event_date >= today)
        .order_by(XaiEventCalendar.event_date.asc())
        .limit(20)
    ).scalars().all()

    events = []
    for e in rows:
        events.append({
            "id": e.id,
            "event_date": e.event_date.isoformat(),
            "event_name": e.event_name,
            "event_type": e.event_type,
            "description": e.description,
            "xrp_relevance": str(e.xrp_relevance) if e.xrp_relevance else None,
            "potential_impact": e.potential_impact,
            "recurring": e.recurring,
        })

    return {"count": len(events), "events": events}


@router.get("/api/xai/ratio")
def get_xai_ratio(db: Session = Depends(get_db)):
    """Get utility-to-speculation ratio — latest + 30-day history."""
    rows = db.execute(
        select(XaiOnchainMetrics)
        .where(XaiOnchainMetrics.utility_to_speculation_ratio.isnot(None))
        .order_by(XaiOnchainMetrics.timestamp.desc())
        .limit(30)
    ).scalars().all()

    history = [
        {
            "timestamp": r.timestamp.isoformat(),
            "ratio": str(r.utility_to_speculation_ratio),
            "utility_volume": str(r.utility_volume_usd) if r.utility_volume_usd else None,
            "speculation_volume": str(r.speculation_volume_usd) if r.speculation_volume_usd else None,
        }
        for r in rows
    ]

    latest = history[0] if history else None

    return {"latest": latest, "history": history}
