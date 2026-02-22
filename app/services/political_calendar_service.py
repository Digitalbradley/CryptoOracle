"""Political calendar service — event management and proximity scoring.

Manages scheduled political/economic events (FOMC, CPI, hearings, elections)
and computes proximity-based scores for the political signal layer.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.political_calendar import PoliticalCalendar

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Known 2026 event dates
# ---------------------------------------------------------------------------

FOMC_2026_DATES = [
    date(2026, 1, 28), date(2026, 1, 29),
    date(2026, 3, 17), date(2026, 3, 18),
    date(2026, 5, 5), date(2026, 5, 6),
    date(2026, 6, 16), date(2026, 6, 17),
    date(2026, 7, 28), date(2026, 7, 29),
    date(2026, 9, 15), date(2026, 9, 16),
    date(2026, 10, 27), date(2026, 10, 28),
    date(2026, 12, 8), date(2026, 12, 9),
]

# CPI release dates are ~12th of each month (approximate)
CPI_2026_DATES = [
    date(2026, 1, 14), date(2026, 2, 12), date(2026, 3, 11),
    date(2026, 4, 14), date(2026, 5, 13), date(2026, 6, 10),
    date(2026, 7, 14), date(2026, 8, 12), date(2026, 9, 10),
    date(2026, 10, 14), date(2026, 11, 12), date(2026, 12, 10),
]

# Jobs report: first Friday of each month
JOBS_2026_DATES = [
    date(2026, 1, 2), date(2026, 2, 6), date(2026, 3, 6),
    date(2026, 4, 3), date(2026, 5, 1), date(2026, 6, 5),
    date(2026, 7, 3), date(2026, 8, 7), date(2026, 9, 4),
    date(2026, 10, 2), date(2026, 11, 6), date(2026, 12, 4),
]

# GDP release: ~end of Jan/Apr/Jul/Oct
GDP_2026_DATES = [
    date(2026, 1, 29), date(2026, 4, 29),
    date(2026, 7, 29), date(2026, 10, 28),
]

# BOJ Monetary Policy Meetings (decision dates, 8x/year)
BOJ_2026_DATES = [
    date(2026, 1, 24), date(2026, 3, 14),
    date(2026, 4, 30), date(2026, 6, 18),
    date(2026, 7, 31), date(2026, 9, 17),
    date(2026, 10, 30), date(2026, 12, 18),
]

# ECB Governing Council Rate Decisions (8x/year)
ECB_2026_DATES = [
    date(2026, 1, 30), date(2026, 3, 12),
    date(2026, 4, 16), date(2026, 6, 4),
    date(2026, 7, 16), date(2026, 9, 10),
    date(2026, 10, 29), date(2026, 12, 10),
]

# OPEC+ Ministerial Meetings (approximate, ~6x/year)
OPEC_2026_DATES = [
    date(2026, 2, 1), date(2026, 4, 3),
    date(2026, 6, 5), date(2026, 8, 7),
    date(2026, 10, 2), date(2026, 12, 4),
]

# Treasury Quarterly Refunding Announcements (4x/year)
TREASURY_REFUND_2026_DATES = [
    date(2026, 2, 4), date(2026, 5, 6),
    date(2026, 8, 5), date(2026, 11, 4),
]


def _build_seed_events(year: int = 2026) -> list[dict]:
    """Build list of seed events for the given year."""
    events = []

    # FOMC meetings (paired days)
    for i in range(0, len(FOMC_2026_DATES), 2):
        day1 = FOMC_2026_DATES[i]
        day2 = FOMC_2026_DATES[i + 1]
        events.append({
            "event_date": day2,  # Decision announced day 2
            "event_type": "fomc_meeting",
            "category": "monetary_policy",
            "title": f"FOMC Meeting ({day1.strftime('%b %d')}-{day2.strftime('%d')}, {year})",
            "description": "Federal Open Market Committee interest rate decision.",
            "country": "US",
            "expected_volatility": "high",
            "crypto_relevance": 8,
            "is_recurring": True,
            "recurrence_rule": "8x/year",
        })

    # CPI releases
    for d in CPI_2026_DATES:
        events.append({
            "event_date": d,
            "event_type": "cpi_release",
            "category": "monetary_policy",
            "title": f"CPI Release ({d.strftime('%b %d')}, {year})",
            "description": "Consumer Price Index data release. Key inflation indicator.",
            "country": "US",
            "expected_volatility": "high",
            "crypto_relevance": 7,
            "is_recurring": True,
            "recurrence_rule": "monthly",
        })

    # Jobs reports
    for d in JOBS_2026_DATES:
        events.append({
            "event_date": d,
            "event_type": "jobs_report",
            "category": "fiscal_policy",
            "title": f"Non-Farm Payrolls ({d.strftime('%b %d')}, {year})",
            "description": "Monthly employment situation report.",
            "country": "US",
            "expected_volatility": "medium",
            "crypto_relevance": 5,
            "is_recurring": True,
            "recurrence_rule": "monthly",
        })

    # GDP releases
    for d in GDP_2026_DATES:
        q_num = (d.month - 1) // 3 + 1
        events.append({
            "event_date": d,
            "event_type": "gdp_release",
            "category": "fiscal_policy",
            "title": f"GDP Release Q{q_num} ({year})",
            "description": f"Gross Domestic Product Q{q_num} estimate.",
            "country": "US",
            "expected_volatility": "medium",
            "crypto_relevance": 5,
            "is_recurring": True,
            "recurrence_rule": "quarterly",
        })

    # US midterm elections (Nov 2026)
    events.append({
        "event_date": date(2026, 11, 3),
        "event_type": "us_election",
        "category": "election",
        "title": "US Midterm Elections (Nov 2026)",
        "description": "US midterm elections — all House seats + 1/3 Senate seats.",
        "country": "US",
        "expected_volatility": "extreme",
        "crypto_relevance": 7,
        "is_recurring": True,
        "recurrence_rule": "2yr",
    })

    # --- Macro-relevant events (Layer 7) ---

    # BOJ rate decisions — carry trade key driver
    for d in BOJ_2026_DATES:
        events.append({
            "event_date": d,
            "event_type": "boj_meeting",
            "category": "monetary_policy",
            "title": f"BOJ Rate Decision ({d.strftime('%b %d')}, {year})",
            "description": "Bank of Japan monetary policy meeting. Key carry trade driver.",
            "country": "JP",
            "expected_volatility": "high",
            "crypto_relevance": 7,
            "is_recurring": True,
            "recurrence_rule": "8x/year",
        })

    # ECB rate decisions
    for d in ECB_2026_DATES:
        events.append({
            "event_date": d,
            "event_type": "ecb_meeting",
            "category": "monetary_policy",
            "title": f"ECB Rate Decision ({d.strftime('%b %d')}, {year})",
            "description": "European Central Bank interest rate decision.",
            "country": "EU",
            "expected_volatility": "medium",
            "crypto_relevance": 5,
            "is_recurring": True,
            "recurrence_rule": "8x/year",
        })

    # OPEC+ meetings — oil supply decisions
    for d in OPEC_2026_DATES:
        events.append({
            "event_date": d,
            "event_type": "opec_meeting",
            "category": "geopolitical",
            "title": f"OPEC+ Ministerial Meeting ({d.strftime('%b %d')}, {year})",
            "description": "OPEC+ production decision. Affects oil prices and inflation.",
            "country": "INTL",
            "expected_volatility": "medium",
            "crypto_relevance": 5,
            "is_recurring": True,
            "recurrence_rule": "6x/year",
        })

    # Treasury quarterly refunding
    for d in TREASURY_REFUND_2026_DATES:
        q_num = (d.month - 1) // 3 + 1
        events.append({
            "event_date": d,
            "event_type": "treasury_refunding",
            "category": "monetary_policy",
            "title": f"Treasury Quarterly Refunding Q{q_num} ({year})",
            "description": "US Treasury auction sizes announced. Affects bond market liquidity.",
            "country": "US",
            "expected_volatility": "medium",
            "crypto_relevance": 4,
            "is_recurring": True,
            "recurrence_rule": "quarterly",
        })

    return events


def seed_recurring_events(db: Session, year: int = 2026, *, commit: bool = True) -> int:
    """Seed calendar with known recurring political/economic events.

    Returns number of events seeded.
    """
    events = _build_seed_events(year)
    count = 0

    for ev in events:
        stmt = pg_insert(PoliticalCalendar).values([ev])
        stmt = stmt.on_conflict_do_update(
            index_elements=["event_date", "event_type"],
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "expected_volatility": stmt.excluded.expected_volatility,
                "crypto_relevance": stmt.excluded.crypto_relevance,
            },
        )
        db.execute(stmt)
        count += 1

    if commit:
        db.commit()
    logger.info("Seeded %d calendar events for %d", count, year)
    return count


def get_upcoming_events(db: Session, days_ahead: int = 7) -> list[dict]:
    """Get upcoming political/economic events within N days."""
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    rows = db.execute(
        select(PoliticalCalendar)
        .where(
            PoliticalCalendar.event_date >= today,
            PoliticalCalendar.event_date <= cutoff,
        )
        .order_by(PoliticalCalendar.event_date.asc())
    ).scalars().all()

    return [
        {
            "id": r.id,
            "event_date": r.event_date.isoformat(),
            "event_type": r.event_type,
            "category": r.category,
            "title": r.title,
            "description": r.description,
            "country": r.country,
            "expected_volatility": r.expected_volatility,
            "expected_direction": r.expected_direction,
            "crypto_relevance": r.crypto_relevance,
            "date_gematria_value": r.date_gematria_value,
            "event_title_gematria": r.event_title_gematria,
        }
        for r in rows
    ]


def get_next_major_event(db: Session) -> dict | None:
    """Get the next high/extreme volatility event."""
    today = date.today()

    row = db.execute(
        select(PoliticalCalendar)
        .where(
            PoliticalCalendar.event_date >= today,
            PoliticalCalendar.expected_volatility.in_(["high", "extreme"]),
        )
        .order_by(PoliticalCalendar.event_date.asc())
        .limit(1)
    ).scalar_one_or_none()

    if not row:
        return None

    days_until = (row.event_date - today).days
    return {
        "event_date": row.event_date.isoformat(),
        "event_type": row.event_type,
        "title": row.title,
        "expected_volatility": row.expected_volatility,
        "days_until": days_until,
        "hours_until": days_until * 24,
    }


def compute_calendar_score(db: Session) -> dict:
    """Compute proximity-based calendar score.

    Score is based on distance to next major event:
    - Event today, volatility "extreme": ±0.8
    - Event today, volatility "high": ±0.5
    - Event within 24h: ±0.3
    - Event within 48h: ±0.15
    - No events within 48h: 0.0

    Returns dict with score and context.
    """
    today = date.today()
    next_2d = today + timedelta(days=2)
    next_7d = today + timedelta(days=7)

    # Events within 2 days (for scoring)
    near_events = db.execute(
        select(PoliticalCalendar)
        .where(
            PoliticalCalendar.event_date >= today,
            PoliticalCalendar.event_date <= next_2d,
        )
        .order_by(PoliticalCalendar.event_date.asc())
    ).scalars().all()

    # Events within 7 days (for context)
    week_events = db.execute(
        select(PoliticalCalendar)
        .where(
            PoliticalCalendar.event_date >= today,
            PoliticalCalendar.event_date <= next_7d,
        )
    ).scalars().all()

    upcoming_7d = len(week_events)
    upcoming_high_impact_7d = sum(
        1 for e in week_events
        if e.expected_volatility in ("high", "extreme")
    )

    # Next major event
    next_major = get_next_major_event(db)
    hours_to_next = next_major["hours_until"] if next_major else None
    next_event_type = next_major["event_type"] if next_major else None

    # Compute score from nearest events
    score = 0.0
    for event in near_events:
        days_until = (event.event_date - today).days
        volatility = event.expected_volatility or "medium"

        # Direction: default neutral (uncertainty tends to be negative for crypto)
        direction = -1.0  # Events create uncertainty → slight bearish default

        if days_until == 0:
            if volatility == "extreme":
                event_score = 0.8 * direction
            elif volatility == "high":
                event_score = 0.5 * direction
            else:
                event_score = 0.3 * direction
        elif days_until == 1:
            if volatility in ("extreme", "high"):
                event_score = 0.3 * direction
            else:
                event_score = 0.15 * direction
        else:  # 2 days
            event_score = 0.15 * direction

        # Use the strongest signal
        if abs(event_score) > abs(score):
            score = event_score

    return {
        "score": round(max(-1.0, min(1.0, score)), 4),
        "hours_to_next": hours_to_next,
        "next_event_type": next_event_type,
        "upcoming_7d": upcoming_7d,
        "upcoming_high_impact_7d": upcoming_high_impact_7d,
    }


def enrich_with_gematria(db: Session, event_id: int) -> None:
    """Compute and store gematria values for a calendar event."""
    from app.services.numerology_compute import GematriaCalculator

    row = db.execute(
        select(PoliticalCalendar).where(PoliticalCalendar.id == event_id)
    ).scalar_one_or_none()

    if not row:
        return

    calc = GematriaCalculator()

    # Title gematria
    if row.title:
        title_gem = calc.calculate_all_ciphers(row.title)
        row.event_title_gematria = title_gem

    # Date gematria: digit sum of YYYYMMDD
    date_str = row.event_date.strftime("%Y%m%d")
    digit_sum = sum(int(d) for d in date_str)
    row.date_gematria_value = digit_sum

    db.commit()
