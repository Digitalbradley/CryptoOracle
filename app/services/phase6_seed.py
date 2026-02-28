"""Phase 6 bootstrap: XAI (XRP Adoption Intelligence) seed data.

Seeds known partnerships, tracked entities, and institutional event calendar.
Then runs initial XRPL data fetch and XAI composite computation.
"""

import logging
from datetime import date, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.xai import XaiEventCalendar, XaiPartnership, XaiTrackedEntity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Known partnerships (from XAI spec Section 6)
# ---------------------------------------------------------------------------
KNOWN_PARTNERSHIPS = [
    # CBDC Partnerships
    {"partner_name": "Royal Monetary Authority of Bhutan", "partner_type": "central_bank",
     "country": "Bhutan", "partnership_type": "cbdc", "pipeline_stage": "pilot",
     "partner_weight": 1.5, "is_cpmi_member_country": False},
    {"partner_name": "Republic of Palau", "partner_type": "central_bank",
     "country": "Palau", "partnership_type": "cbdc", "pipeline_stage": "pilot",
     "partner_weight": 1.0, "is_cpmi_member_country": False},
    {"partner_name": "National Bank of Georgia", "partner_type": "central_bank",
     "country": "Georgia", "partnership_type": "cbdc", "pipeline_stage": "announced",
     "partner_weight": 1.5, "is_cpmi_member_country": False},
    {"partner_name": "Banco de la República Colombia", "partner_type": "central_bank",
     "country": "Colombia", "partnership_type": "cbdc", "pipeline_stage": "announced",
     "partner_weight": 2.0, "is_cpmi_member_country": False},
    {"partner_name": "Central Bank of Montenegro", "partner_type": "central_bank",
     "country": "Montenegro", "partnership_type": "cbdc", "pipeline_stage": "announced",
     "partner_weight": 1.5, "is_cpmi_member_country": False},
    # Major Bank Partners
    {"partner_name": "BNY Mellon", "partner_type": "bank",
     "country": "US", "partnership_type": "custody", "pipeline_stage": "production",
     "partner_weight": 2.5, "is_cpmi_member_country": False},
    {"partner_name": "SBI Holdings", "partner_type": "bank",
     "country": "Japan", "partnership_type": "odl", "pipeline_stage": "production",
     "partner_weight": 2.5, "is_cpmi_member_country": True},
    {"partner_name": "Santander", "partner_type": "bank",
     "country": "Spain", "partnership_type": "ripplenet", "pipeline_stage": "production",
     "partner_weight": 2.0, "is_cpmi_member_country": True},
    {"partner_name": "Standard Chartered", "partner_type": "bank",
     "country": "UK", "partnership_type": "ripplenet", "pipeline_stage": "production",
     "partner_weight": 2.0, "is_cpmi_member_country": True},
    {"partner_name": "CIBC", "partner_type": "bank",
     "country": "Canada", "partnership_type": "ripplenet", "pipeline_stage": "production",
     "partner_weight": 2.0, "is_cpmi_member_country": True},
    {"partner_name": "HSBC", "partner_type": "bank",
     "country": "UK", "partnership_type": "custody", "pipeline_stage": "production",
     "partner_weight": 2.0, "is_cpmi_member_country": True},
    # RLUSD Partners
    {"partner_name": "SBI (RLUSD Japan)", "partner_type": "bank",
     "country": "Japan", "partnership_type": "rlusd", "pipeline_stage": "announced",
     "partner_weight": 2.5, "is_cpmi_member_country": True},
    # Acquisitions
    {"partner_name": "Hidden Road", "partner_type": "fintech",
     "country": "US", "partnership_type": "acquisition", "pipeline_stage": "production",
     "partner_weight": 2.0, "is_cpmi_member_country": False},
    # Payment Providers
    {"partner_name": "Tranglo", "partner_type": "payment_provider",
     "country": "Malaysia", "partnership_type": "odl", "pipeline_stage": "production",
     "partner_weight": 1.5, "is_cpmi_member_country": False},
    {"partner_name": "Onafriq", "partner_type": "payment_provider",
     "country": "Africa", "partnership_type": "odl", "pipeline_stage": "production",
     "partner_weight": 1.5, "is_cpmi_member_country": False},
]

# Stage scores
STAGE_SCORES = {"announced": 0.15, "pilot": 0.50, "production": 1.00}


# ---------------------------------------------------------------------------
# Tracked entities (from XAI spec Section 2.2)
# ---------------------------------------------------------------------------
TRACKED_ENTITIES = [
    # Tier 1 — Direct Policy Authority
    {"entity_type": "person", "name": "Fabio Panetta", "role": "Bank of Italy Governor, CPMI Chair",
     "institution": "Bank of Italy / BIS CPMI", "tier": 1, "category": "cpmi",
     "country": "Italy", "cpmi_member": True, "fsb_member": True},
    {"entity_type": "person", "name": "Andrew Bailey", "role": "Bank of England Governor, FSB Chair",
     "institution": "Bank of England / FSB", "tier": 1, "category": "fsb",
     "country": "UK", "cpmi_member": True, "fsb_member": True},
    {"entity_type": "person", "name": "Tara Rice", "role": "BIS CPMI Head of Secretariat",
     "institution": "BIS", "tier": 1, "category": "cpmi",
     "country": "Switzerland", "cpmi_member": True, "fsb_member": False},
    {"entity_type": "person", "name": "Tobias Adrian", "role": "IMF Financial Counsellor",
     "institution": "IMF", "tier": 1, "category": "fsb",
     "country": "US", "cpmi_member": False, "fsb_member": True},
    # Tier 2 — Key Ripple Markets
    {"entity_type": "person", "name": "Der Jiun Chia", "role": "MAS Managing Director",
     "institution": "MAS", "tier": 2, "category": "central_bank",
     "country": "Singapore", "cpmi_member": True, "fsb_member": True},
    {"entity_type": "person", "name": "Ryozo Himino", "role": "BOJ Deputy Governor",
     "institution": "Bank of Japan", "tier": 2, "category": "central_bank",
     "country": "Japan", "cpmi_member": True, "fsb_member": True},
    {"entity_type": "person", "name": "Gabriel Galípolo", "role": "Central Bank of Brazil Governor",
     "institution": "Central Bank of Brazil", "tier": 2, "category": "central_bank",
     "country": "Brazil", "cpmi_member": True, "fsb_member": True},
    {"entity_type": "person", "name": "Paul Atkins", "role": "SEC Chairman",
     "institution": "SEC", "tier": 2, "category": "regulator",
     "country": "US", "cpmi_member": False, "fsb_member": True},
    {"entity_type": "person", "name": "Michelle Bowman", "role": "Fed Governor",
     "institution": "Federal Reserve", "tier": 2, "category": "central_bank",
     "country": "US", "cpmi_member": True, "fsb_member": True},
    # Tier 3 — Ripple Executives
    {"entity_type": "person", "name": "Brad Garlinghouse", "role": "Ripple CEO",
     "institution": "Ripple", "tier": 3, "category": "ripple",
     "country": "US", "cpmi_member": False, "fsb_member": False},
    {"entity_type": "person", "name": "Monica Long", "role": "Ripple President",
     "institution": "Ripple", "tier": 3, "category": "ripple",
     "country": "US", "cpmi_member": False, "fsb_member": False},
    {"entity_type": "person", "name": "David Schwartz", "role": "Ripple CTO",
     "institution": "Ripple", "tier": 3, "category": "ripple",
     "country": "US", "cpmi_member": False, "fsb_member": False},
    {"entity_type": "person", "name": "Stuart Alderoty", "role": "Ripple CLO",
     "institution": "Ripple", "tier": 3, "category": "ripple",
     "country": "US", "cpmi_member": False, "fsb_member": False},
]


# ---------------------------------------------------------------------------
# Institutional event calendar
# ---------------------------------------------------------------------------
INSTITUTIONAL_EVENTS = [
    # 2026 dates (approximate — update with actual dates as announced)
    {"event_date": date(2026, 3, 15), "event_name": "FSB Plenary Meeting (Q1)",
     "event_type": "fsb_plenary", "xrp_relevance": 0.8, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "~3x/year"},
    {"event_date": date(2026, 4, 2), "event_name": "CPMI Committee Meeting (Q2)",
     "event_type": "cpmi_meeting", "xrp_relevance": 0.9, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "~4x/year"},
    {"event_date": date(2026, 4, 16), "event_name": "G20 Finance Ministers / Central Bank Governors",
     "event_type": "g20", "xrp_relevance": 0.7, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "2x/year"},
    {"event_date": date(2026, 5, 1), "event_name": "XRP Escrow Release (May)",
     "event_type": "escrow_release", "xrp_relevance": 0.6, "potential_impact": "medium",
     "recurring": True, "recurrence_pattern": "monthly"},
    {"event_date": date(2026, 6, 1), "event_name": "XRP Escrow Release (June)",
     "event_type": "escrow_release", "xrp_relevance": 0.6, "potential_impact": "medium",
     "recurring": True, "recurrence_pattern": "monthly"},
    {"event_date": date(2026, 7, 15), "event_name": "FSB Plenary Meeting (Q2)",
     "event_type": "fsb_plenary", "xrp_relevance": 0.8, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "~3x/year"},
    {"event_date": date(2026, 10, 1), "event_name": "FSB Annual Progress Report on Cross-Border Payments",
     "event_type": "fsb_report", "xrp_relevance": 0.9, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "annual (October)"},
    {"event_date": date(2026, 10, 12), "event_name": "IMF/World Bank Annual Meetings",
     "event_type": "imf_worldbank", "xrp_relevance": 0.7, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "annual (October)"},
    {"event_date": date(2026, 10, 26), "event_name": "SWIFT Sibos Conference",
     "event_type": "sibos", "xrp_relevance": 0.6, "potential_impact": "medium",
     "recurring": True, "recurrence_pattern": "annual (October)"},
    {"event_date": date(2026, 11, 1), "event_name": "Ripple Swell Conference (estimated)",
     "event_type": "ripple_event", "xrp_relevance": 1.0, "potential_impact": "high",
     "recurring": True, "recurrence_pattern": "annual"},
]


def seed_partnerships(db: Session) -> int:
    """Seed known Ripple partnerships."""
    count = 0
    for p in KNOWN_PARTNERSHIPS:
        row = {
            "partner_name": p["partner_name"],
            "partner_type": p["partner_type"],
            "country": p.get("country"),
            "is_cpmi_member_country": p.get("is_cpmi_member_country", False),
            "partnership_type": p.get("partnership_type"),
            "pipeline_stage": p["pipeline_stage"],
            "stage_score": STAGE_SCORES.get(p["pipeline_stage"], 0),
            "partner_weight": p.get("partner_weight", 1.0),
            "notes": "Pre-seeded from XAI spec",
        }
        stmt = pg_insert(XaiPartnership).values([row])
        stmt = stmt.on_conflict_do_nothing()  # skip if already exists
        result = db.execute(stmt)
        count += result.rowcount
    db.commit()
    logger.info("Seeded %d partnerships", count)
    return count


def seed_tracked_entities(db: Session) -> int:
    """Seed key tracked people/institutions."""
    count = 0
    for e in TRACKED_ENTITIES:
        stmt = pg_insert(XaiTrackedEntity).values([e])
        stmt = stmt.on_conflict_do_nothing()
        result = db.execute(stmt)
        count += result.rowcount
    db.commit()
    logger.info("Seeded %d tracked entities", count)
    return count


def seed_event_calendar(db: Session) -> int:
    """Seed institutional event calendar."""
    count = 0
    for ev in INSTITUTIONAL_EVENTS:
        stmt = pg_insert(XaiEventCalendar).values([ev])
        stmt = stmt.on_conflict_do_nothing()
        result = db.execute(stmt)
        count += result.rowcount
    db.commit()
    logger.info("Seeded %d calendar events", count)
    return count


def run_phase6_bootstrap(db: Session) -> dict:
    """Full Phase 6 bootstrap: seed data + initial XAI computation."""
    results = {}

    # 1. Seed partnerships
    results["partnerships_seeded"] = seed_partnerships(db)

    # 2. Seed tracked entities
    results["entities_seeded"] = seed_tracked_entities(db)

    # 3. Seed event calendar
    results["calendar_events_seeded"] = seed_event_calendar(db)

    # 4. Fetch initial XRPL data
    try:
        from app.services.xrpl_fetch import fetch_and_store
        xrpl_result = fetch_and_store(db)
        results["xrpl_fetch"] = xrpl_result
    except Exception:
        logger.exception("XRPL initial fetch failed (non-fatal)")
        results["xrpl_fetch"] = "failed"

    # 5. Compute initial XAI composite
    try:
        from app.services.xai_signal_service import compute_xai_composite
        xai_result = compute_xai_composite(db)
        results["xai_score"] = xai_result["xai_score"]
        results["adoption_phase"] = xai_result["adoption_phase"]
    except Exception:
        logger.exception("Initial XAI computation failed (non-fatal)")
        results["xai_score"] = "failed"

    logger.info("Phase 6 bootstrap complete: %s", results)
    return results
