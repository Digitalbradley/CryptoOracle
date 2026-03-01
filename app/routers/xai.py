"""XAI (XRP Adoption Intelligence) router — on-chain metrics, partnerships, events, policies."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.xai import (
    XaiComposite,
    XaiEventCalendar,
    XaiOnchainMetrics,
    XaiPartnership,
    XaiPolicyEvent,
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
        "xai_score": str(row.xai_score) if row.xai_score is not None else None,
        "policy_pipeline_score": str(row.policy_pipeline_score) if row.policy_pipeline_score is not None else None,
        "partnership_deployment_score": str(row.partnership_deployment_score) if row.partnership_deployment_score is not None else None,
        "onchain_utility_score": str(row.onchain_utility_score) if row.onchain_utility_score is not None else None,
        "personnel_intelligence_score": str(row.personnel_intelligence_score) if row.personnel_intelligence_score is not None else None,
        "utility_to_speculation_ratio": str(row.utility_to_speculation_ratio) if row.utility_to_speculation_ratio is not None else None,
        "rlusd_market_cap": str(row.rlusd_market_cap) if row.rlusd_market_cap is not None else None,
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
        "xrpl_payment_volume_usd": str(row.xrpl_payment_volume_usd) if row.xrpl_payment_volume_usd is not None else None,
        "xrpl_dex_volume_usd": str(row.xrpl_dex_volume_usd) if row.xrpl_dex_volume_usd is not None else None,
        "rlusd_total_supply": str(row.rlusd_total_supply) if row.rlusd_total_supply is not None else None,
        "rlusd_unique_holders": row.rlusd_unique_holders,
        "rlusd_trust_line_count": row.rlusd_trust_line_count,
        "utility_volume_usd": str(row.utility_volume_usd) if row.utility_volume_usd is not None else None,
        "speculation_volume_usd": str(row.speculation_volume_usd) if row.speculation_volume_usd is not None else None,
        "utility_to_speculation_ratio": str(row.utility_to_speculation_ratio) if row.utility_to_speculation_ratio is not None else None,
        "xrpl_active_addresses": row.xrpl_active_addresses,
        "xrpl_new_accounts": row.xrpl_new_accounts,
        "xrp_exchange_reserve": str(row.xrp_exchange_reserve) if row.xrp_exchange_reserve is not None else None,
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
            "stage_score": str(p.stage_score) if p.stage_score is not None else None,
            "partner_weight": str(p.partner_weight) if p.partner_weight is not None else None,
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
            "xrp_relevance": str(e.xrp_relevance) if e.xrp_relevance is not None else None,
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
            "utility_volume": str(r.utility_volume_usd) if r.utility_volume_usd is not None else None,
            "speculation_volume": str(r.speculation_volume_usd) if r.speculation_volume_usd is not None else None,
        }
        for r in rows
    ]

    latest = history[0] if history else None

    return {"latest": latest, "history": history}


@router.get("/api/xai/policies")
def get_xai_policies(days: int = 90, db: Session = Depends(get_db)):
    """Get recent classified policy/regulatory events."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(XaiPolicyEvent)
        .where(XaiPolicyEvent.timestamp >= cutoff)
        .order_by(XaiPolicyEvent.timestamp.desc())
        .limit(50)
    ).scalars().all()

    events = []
    for e in rows:
        events.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "source": e.source,
            "event_type": e.event_type,
            "title": e.title,
            "url": e.url,
            "cross_border_relevance": str(e.cross_border_relevance) if e.cross_border_relevance is not None else None,
            "dlt_favorability": str(e.dlt_favorability) if e.dlt_favorability is not None else None,
            "stablecoin_stance": str(e.stablecoin_stance) if e.stablecoin_stance is not None else None,
            "regulatory_direction": str(e.regulatory_direction) if e.regulatory_direction is not None else None,
            "timeline_urgency": str(e.timeline_urgency) if e.timeline_urgency is not None else None,
            "xrp_mentioned": e.xrp_mentioned,
            "policy_impact_score": str(e.policy_impact_score) if e.policy_impact_score is not None else None,
        })

    return {"count": len(events), "events": events}


@router.post("/api/xai/recompute")
def recompute_xai(db: Session = Depends(get_db)):
    """Force XRPL fetch + policy scrape + XAI composite recompute."""
    results = {}

    # 1. Fetch XRPL data
    try:
        from app.services.xrpl_fetch import fetch_and_store
        results["xrpl_fetch"] = fetch_and_store(db)
    except Exception as exc:
        import traceback as tb
        db.rollback()
        results["xrpl_fetch"] = {"error": str(exc), "traceback": tb.format_exc()}

    # 2. Scrape + classify policy events
    try:
        from app.services.xai_policy_fetch import fetch_and_classify
        results["policy_scrape"] = fetch_and_classify(db)
    except Exception as exc:
        import traceback as tb
        db.rollback()
        results["policy_scrape"] = {"error": str(exc), "traceback": tb.format_exc()}

    # 3. Recompute XAI composite
    try:
        from app.services.xai_signal_service import compute_xai_composite
        composite = compute_xai_composite(db)
        results["xai_score"] = composite["xai_score"]
        results["adoption_phase"] = composite["adoption_phase"]
        results["policy_pipeline_score"] = composite["policy_pipeline_score"]
        results["rlusd_market_cap"] = composite["rlusd_market_cap"]
    except Exception as exc:
        import traceback as tb
        db.rollback()
        results["composite"] = {"error": str(exc), "traceback": tb.format_exc()}

    return results
