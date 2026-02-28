"""XAI signal computation — computes sub-signals and composite XAI score.

Phase A: on-chain utility + partnership deployment scores.
Phase B: + policy pipeline score.
Phase C will add: personnel intelligence score.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.xai import (
    XaiComposite,
    XaiOnchainMetrics,
    XaiPartnership,
    XaiPolicyEvent,
)

logger = logging.getLogger(__name__)

# Stage scores for partnership pipeline
STAGE_SCORES = {
    "announced": Decimal("0.15"),
    "pilot": Decimal("0.50"),
    "production": Decimal("1.00"),
}

# XAI sub-signal weights (Phase A: only on-chain + partnerships active)
FULL_WEIGHTS = {
    "policy_pipeline": Decimal("0.15"),
    "partnerships": Decimal("0.25"),
    "onchain_utility": Decimal("0.40"),
    "personnel": Decimal("0.20"),
}

# Utility-to-speculation ratio scoring thresholds
RATIO_THRESHOLDS = [
    (Decimal("1.00"), Decimal("1.0")),
    (Decimal("0.50"), Decimal("0.8")),
    (Decimal("0.25"), Decimal("0.6")),
    (Decimal("0.10"), Decimal("0.3")),
    (Decimal("0.05"), Decimal("0.0")),
    (Decimal("0.01"), Decimal("-0.2")),
]
# Below 0.01 → -0.5


def compute_onchain_utility_score(db: Session) -> float:
    """Score on-chain utility metrics from latest xai_onchain_metrics row.

    Primary driver: utility-to-speculation ratio.
    Secondary: RLUSD supply growth, trust line count.
    Returns -1.0 to +1.0.
    """
    row = db.execute(
        select(XaiOnchainMetrics)
        .order_by(XaiOnchainMetrics.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not row:
        return 0.0

    # Primary: utility/speculation ratio
    ratio = float(row.utility_to_speculation_ratio or 0)
    ratio_dec = Decimal(str(ratio))

    ratio_score = Decimal("-0.5")  # default: below 0.01
    for threshold, score in RATIO_THRESHOLDS:
        if ratio_dec >= threshold:
            ratio_score = score
            break

    # Secondary: RLUSD supply (bonus for growth)
    rlusd_bonus = Decimal("0")
    supply = float(row.rlusd_total_supply or 0)
    if supply > 1_000_000_000:  # > $1B
        rlusd_bonus = Decimal("0.15")
    elif supply > 500_000_000:
        rlusd_bonus = Decimal("0.10")
    elif supply > 100_000_000:
        rlusd_bonus = Decimal("0.05")

    # Secondary: trust line adoption
    trust_bonus = Decimal("0")
    trust_lines = row.rlusd_trust_line_count or 0
    if trust_lines > 100_000:
        trust_bonus = Decimal("0.10")
    elif trust_lines > 10_000:
        trust_bonus = Decimal("0.05")

    score = float(ratio_score + rlusd_bonus + trust_bonus)
    return max(-1.0, min(1.0, round(score, 4)))


def compute_partnership_score(db: Session) -> float:
    """Score the partnership pipeline from xai_partnerships.

    Weighted sum of (stage_score * partner_weight), normalized.
    Returns -1.0 to +1.0.
    """
    partnerships = db.execute(select(XaiPartnership)).scalars().all()

    if not partnerships:
        return 0.0

    weighted_sum = Decimal("0")
    max_possible = Decimal("0")

    for p in partnerships:
        stage = STAGE_SCORES.get(p.pipeline_stage, Decimal("0"))
        weight = p.partner_weight or Decimal("1.0")
        weighted_sum += stage * weight
        max_possible += Decimal("1.0") * weight  # max is production (1.0) for all

    if max_possible == 0:
        return 0.0

    # Normalize to 0-1 range, then shift to -0.5 to +0.5 range
    # (so a "normal" pipeline produces a mildly positive score)
    raw = weighted_sum / max_possible  # 0 to 1
    score = float(raw * 2 - 1)  # -1 to +1

    return max(-1.0, min(1.0, round(score, 4)))


def compute_policy_pipeline_score(db: Session, days_window: int = 90) -> float | None:
    """Score the regulatory/policy pipeline from recent xai_policy_events.

    Weighted average of policy_impact_score, weighted by
    (cross_border_relevance + timeline_urgency) and recency.
    Returns -1.0 to +1.0, or None if no policy data exists.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_window)

    rows = db.execute(
        select(XaiPolicyEvent)
        .where(
            XaiPolicyEvent.timestamp >= cutoff,
            XaiPolicyEvent.policy_impact_score.isnot(None),
        )
        .order_by(XaiPolicyEvent.timestamp.desc())
    ).scalars().all()

    if not rows:
        return None  # No data yet — signal not active

    total_weight = 0.0
    weighted_sum = 0.0

    for r in rows:
        impact = float(r.policy_impact_score or 0)
        relevance = float(r.cross_border_relevance or 0.5)
        urgency = float(r.timeline_urgency or 0.3)

        # Recency decay: newer events count more
        age_days = (datetime.now(timezone.utc) - r.timestamp).days
        recency = max(0.1, 1.0 - (age_days / days_window))

        # XRP mention boost
        xrp_boost = 1.5 if r.xrp_mentioned else 1.0

        weight = (relevance + urgency) * recency * xrp_boost
        weighted_sum += impact * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(max(-1.0, min(1.0, weighted_sum / total_weight)), 4)


def determine_adoption_phase(ratio: float, xai_score: float) -> str:
    """Classify the current adoption phase."""
    if ratio > 1.0:
        return "stable_utility"
    if ratio > 0.5 or xai_score > 0.7:
        return "stability_approaching"
    if ratio > 0.25 or xai_score > 0.5:
        return "institutional_scale"
    if ratio > 0.10 or xai_score > 0.3:
        return "accelerating"
    if ratio > 0.05 or xai_score > 0.1:
        return "early_adoption"
    return "pre_adoption"


def compute_xai_composite(db: Session) -> dict:
    """Compute the weighted XAI composite score and store it.

    Returns dict with all sub-signals, composite, and adoption phase.
    """
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    # Compute available sub-signals
    onchain_score = compute_onchain_utility_score(db)
    partnership_score = compute_partnership_score(db)
    policy_score = compute_policy_pipeline_score(db)

    # Build available signals — only include those with data
    available = {
        "onchain_utility": (onchain_score, FULL_WEIGHTS["onchain_utility"]),
        "partnerships": (partnership_score, FULL_WEIGHTS["partnerships"]),
    }
    if policy_score is not None:
        available["policy_pipeline"] = (policy_score, FULL_WEIGHTS["policy_pipeline"])

    total_weight = sum(w for _, w in available.values())

    if total_weight > 0:
        composite = sum(
            Decimal(str(score)) * (weight / total_weight)
            for score, weight in available.values()
        )
        xai_score = float(max(Decimal("-1"), min(Decimal("1"), composite)))
    else:
        xai_score = 0.0

    # Get key metrics for storage
    onchain_row = db.execute(
        select(XaiOnchainMetrics)
        .order_by(XaiOnchainMetrics.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    ratio = float(onchain_row.utility_to_speculation_ratio or 0) if onchain_row else 0.0
    rlusd_cap = float(onchain_row.rlusd_total_supply or 0) if onchain_row else 0.0

    # Partnership counts
    total_partners = db.execute(
        select(func.count()).select_from(XaiPartnership)
    ).scalar() or 0
    prod_partners = db.execute(
        select(func.count()).select_from(XaiPartnership)
        .where(XaiPartnership.pipeline_stage == "production")
    ).scalar() or 0

    phase = determine_adoption_phase(ratio, xai_score)

    policy_rounded = round(policy_score, 4) if policy_score is not None else None

    result = {
        "policy_pipeline_score": policy_rounded,
        "partnership_deployment_score": round(partnership_score, 4),
        "onchain_utility_score": round(onchain_score, 4),
        "personnel_intelligence_score": None,
        "xai_score": round(xai_score, 4),
        "utility_to_speculation_ratio": round(ratio, 6),
        "rlusd_market_cap": round(rlusd_cap, 2),
        "active_partnership_count": total_partners,
        "partnerships_in_production": prod_partners,
        "adoption_phase": phase,
        "weights": {k: str(v) for k, v in FULL_WEIGHTS.items()},
    }

    # Store
    policy_dec = Decimal(str(policy_score)) if policy_score is not None else None
    row = {
        "timestamp": now,
        "policy_pipeline_score": policy_dec,
        "partnership_deployment_score": Decimal(str(partnership_score)),
        "onchain_utility_score": Decimal(str(onchain_score)),
        "personnel_intelligence_score": None,
        "xai_score": Decimal(str(xai_score)),
        "utility_to_speculation_ratio": Decimal(str(ratio)),
        "rlusd_market_cap": Decimal(str(rlusd_cap)),
        "active_partnership_count": total_partners,
        "partnerships_in_production": prod_partners,
        "adoption_phase": phase,
        "weights": result["weights"],
    }

    stmt = pg_insert(XaiComposite).values([row])
    stmt = stmt.on_conflict_do_update(
        index_elements=["timestamp"],
        set_={k: stmt.excluded.__getattr__(k) for k in row if k != "timestamp"},
    )
    db.execute(stmt)
    db.commit()

    logger.info(
        "XAI composite: score=%.4f phase=%s ratio=%.6f partners=%d/%d policy=%s",
        xai_score, phase, ratio, prod_partners, total_partners,
        policy_rounded,
    )

    return result
