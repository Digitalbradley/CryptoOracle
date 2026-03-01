"""XAI Phase C: Personnel intelligence scraper + classification.

Data sources (free, no API keys):
1. Ripple blog/newsroom for executive statements
2. BIS speeches page for CPMI Chair statements
3. FSB press releases for FSB Chair statements

Classification via Claude Haiku when Anthropic key is available,
with keyword-based fallback otherwise.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.xai import XaiPersonnelIntelligence, XaiTrackedEntity

logger = logging.getLogger(__name__)

TIMEOUT = 20
HEADERS = {
    "User-Agent": "CryptoOracle/1.0 (Research Bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Keywords for filtering relevant content
_RELEVANCE_KEYWORDS = re.compile(
    r"(?i)\b("
    r"cross.?border|payment|stablecoin|cbdc|digital.?currency|"
    r"dlt|distributed.?ledger|blockchain|crypto.?asset|"
    r"tokeniz|ripple|xrp|rlusd|iso.?20022|"
    r"settlement|clearing|correspondent|remittance|"
    r"innovation|fintech|interoperab"
    r")\b"
)

# Tracked person name patterns for matching
_TRACKED_NAMES: dict[str, dict] = {}  # populated on first run


def _load_tracked_entities(db: Session) -> dict[str, dict]:
    """Load tracked entities and build a name lookup."""
    global _TRACKED_NAMES
    if _TRACKED_NAMES:
        return _TRACKED_NAMES

    rows = db.execute(select(XaiTrackedEntity)).scalars().all()
    for r in rows:
        # Index by last name and full name for flexible matching
        _TRACKED_NAMES[r.name.lower()] = {
            "entity_id": r.id,
            "name": r.name,
            "role": r.role,
            "tier": r.tier,
            "influence_weight": {1: 3.0, 2: 2.0, 3: 1.5}.get(r.tier, 1.0),
        }
        # Also index by last name alone
        parts = r.name.split()
        if len(parts) >= 2:
            _TRACKED_NAMES[parts[-1].lower()] = _TRACKED_NAMES[r.name.lower()]

    return _TRACKED_NAMES


# ---------------------------------------------------------------------------
# Source scrapers
# ---------------------------------------------------------------------------

def fetch_ripple_newsroom() -> list[dict]:
    """Fetch Ripple blog/insights for executive statements."""
    articles = []
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed — Ripple newsroom fetch skipped")
        return []

    try:
        feed = feedparser.parse("https://ripple.com/insights/feed/")
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}"

            if not _RELEVANCE_KEYWORDS.search(text):
                continue

            published = entry.get("published_parsed")
            if published:
                from time import mktime
                ts = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source_title": title[:500],
                "source_url": entry.get("link", ""),
                "summary": summary[:2000] if summary else None,
                "statement_type": "publication",
                "source_label": "Ripple Insights",
            })

        logger.info("Ripple newsroom: found %d relevant articles", len(articles))
    except Exception:
        logger.exception("Error fetching Ripple newsroom")

    return articles


def fetch_bis_speeches() -> list[dict]:
    """Scrape BIS speeches for CPMI/central bank statements."""
    articles = []
    try:
        resp = httpx.get(
            "https://www.bis.org/speeches/index.htm",
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text

        # BIS speech entries: link + speaker + date
        pattern = re.compile(
            r'<a\s+href="(/speeches/sp\d+[a-z]?\.htm)"[^>]*>(.*?)</a>'
            r'.*?<div[^>]*class="[^"]*info[^"]*"[^>]*>(.*?)</div>',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            url_path, title, info = match.groups()
            title = re.sub(r"<[^>]+>", "", title).strip()
            info = re.sub(r"<[^>]+>", "", info).strip()

            if not title:
                continue

            # Filter for relevant content
            combined = f"{title} {info}"
            if not _RELEVANCE_KEYWORDS.search(combined):
                continue

            # Try to extract date
            date_match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", info)
            if date_match:
                try:
                    ts = datetime.strptime(date_match.group(1), "%d %B %Y").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    ts = datetime.now(timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source_title": title[:500],
                "source_url": f"https://www.bis.org{url_path}",
                "summary": info[:1000] if info else None,
                "statement_type": "speech",
                "source_label": "BIS",
                "speaker_info": info,
            })

        logger.info("BIS speeches: found %d relevant entries", len(articles))
    except Exception:
        logger.exception("Error scraping BIS speeches")

    return articles


def fetch_fsb_press() -> list[dict]:
    """Scrape FSB press releases and speeches."""
    articles = []
    try:
        resp = httpx.get(
            "https://www.fsb.org/press/",
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text

        pattern = re.compile(
            r'<a\s+href="(https://www\.fsb\.org/[^"]+)"[^>]*>\s*(.*?)\s*</a>'
            r'.*?<time[^>]*>(.*?)</time>',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            url, title, date_str = match.groups()
            title = re.sub(r"<[^>]+>", "", title).strip()
            if not title:
                continue

            if not _RELEVANCE_KEYWORDS.search(title):
                continue

            try:
                ts = datetime.strptime(date_str.strip(), "%d %B %Y").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                try:
                    ts = datetime.strptime(date_str.strip(), "%B %d, %Y").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source_title": title[:500],
                "source_url": url,
                "summary": None,
                "statement_type": "press_release",
                "source_label": "FSB",
            })

        logger.info("FSB press: found %d relevant entries", len(articles))
    except Exception:
        logger.exception("Error scraping FSB press releases")

    return articles


# ---------------------------------------------------------------------------
# Person matching
# ---------------------------------------------------------------------------

def match_person(text: str, tracked: dict[str, dict]) -> dict | None:
    """Try to match a tracked entity mentioned in the text."""
    text_lower = text.lower()
    for name_key, info in tracked.items():
        if name_key in text_lower:
            return info
    return None


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

_FAVORABLE_KW = re.compile(
    r"(?i)\b(adopt|embrace|framework|clarity|approve|enable|"
    r"support|innovation|pilot|launch|partner|interoperab|"
    r"iso.?20022|real.?time|instant|efficient|progress)\b"
)
_UNFAVORABLE_KW = re.compile(
    r"(?i)\b(ban|restrict|prohibit|crack.?down|enforce|"
    r"concern|risk|warn|delay|reject|oppose|threat|"
    r"sanction|fine|penalty|cautious|prudent)\b"
)
_XRP_KW = re.compile(
    r"(?i)\b(xrp|ripple|rlusd|xrpl|odl|on.?demand.?liquidity)\b"
)


def _keyword_classify_personnel(title: str, summary: str | None = None) -> dict:
    """Keyword-based personnel statement classification (fallback)."""
    text = f"{title} {summary or ''}"

    cb = len(re.findall(r"(?i)\b(cross.?border|payment|remittance|settlement)\b", text))
    cross_border = min(1.0, cb * 0.25)

    fav = len(_FAVORABLE_KW.findall(text))
    unfav = len(_UNFAVORABLE_KW.findall(text))
    total = fav + unfav
    dlt_fav = ((fav - unfav) / total) if total > 0 else 0.0

    sc = len(re.findall(r"(?i)\b(stablecoin|cbdc|rlusd|digital.?dollar|digital.?euro)\b", text))
    stablecoin = min(1.0, sc * 0.3) * (1.0 if fav >= unfav else -1.0)

    urgency = len(re.findall(
        r"(?i)\b(imminent|immediate|final|enacted|deadline|Q[1-4]|2026|2025|timeline)\b", text
    ))
    timeline = min(1.0, urgency * 0.25)

    xrp_mentioned = bool(_XRP_KW.search(text))

    sentiment = (
        cross_border * 0.20
        + dlt_fav * 0.30
        + stablecoin * 0.25
        + timeline * 0.25
    )
    if xrp_mentioned:
        sentiment *= 1.3

    return {
        "cross_border_urgency": round(cross_border, 2),
        "dlt_favorability": round(dlt_fav, 2),
        "stablecoin_stance": round(stablecoin, 2),
        "timeline_urgency": round(timeline, 2),
        "xrp_mentioned": xrp_mentioned,
        "sentiment_score": round(max(-1.0, min(1.0, sentiment)), 2),
    }


def classify_personnel_statement(title: str, summary: str | None = None) -> dict:
    """Classify a personnel statement for XRP adoption impact.

    Uses Claude Haiku if available, falls back to keyword classification.
    """
    if not settings.anthropic_api_key:
        return _keyword_classify_personnel(title, summary)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        prompt = (
            "Classify this statement/speech by a key financial decision-maker "
            "for its impact on XRP/Ripple institutional adoption.\n\n"
            f"Title: {title}\n"
            f"Summary: {summary or 'N/A'}\n\n"
            "Respond with ONLY a JSON object (no markdown):\n"
            '{"cross_border_urgency": <0.0-1.0, urgency around cross-border payment reform>, '
            '"dlt_favorability": <-1.0 to 1.0, positive=favorable to DLT/blockchain>, '
            '"stablecoin_stance": <-1.0 to 1.0, positive=favorable to stablecoins>, '
            '"timeline_urgency": <0.0-1.0, how soon this could affect adoption>, '
            '"xrp_mentioned": <true/false, XRP/Ripple/RLUSD directly mentioned>, '
            '"sentiment_score": <-1.0 to 1.0, overall impact on XRP adoption>}'
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)

        return {
            "cross_border_urgency": float(result.get("cross_border_urgency", 0.5)),
            "dlt_favorability": float(result.get("dlt_favorability", 0.0)),
            "stablecoin_stance": float(result.get("stablecoin_stance", 0.0)),
            "timeline_urgency": float(result.get("timeline_urgency", 0.3)),
            "xrp_mentioned": bool(result.get("xrp_mentioned", False)),
            "sentiment_score": float(result.get("sentiment_score", 0.0)),
        }
    except Exception:
        logger.exception("Claude personnel classification failed, using keyword fallback")
        return _keyword_classify_personnel(title, summary)


# ---------------------------------------------------------------------------
# Main fetch + classify + store
# ---------------------------------------------------------------------------

def fetch_and_classify(db: Session) -> dict:
    """Fetch personnel statements from all sources, classify, and store.

    Returns summary dict with counts.
    """
    tracked = _load_tracked_entities(db)
    all_articles: list[dict] = []

    # Fetch from all sources
    all_articles.extend(fetch_ripple_newsroom())
    all_articles.extend(fetch_bis_speeches())
    all_articles.extend(fetch_fsb_press())

    if not all_articles:
        logger.info("No XAI personnel articles found from any source")
        return {"total": 0, "classified": 0, "matched_persons": 0}

    classified = 0
    matched = 0

    for article in all_articles:
        try:
            # Try to match a tracked person
            combined = f"{article['source_title']} {article.get('summary', '') or ''} {article.get('speaker_info', '')}"
            person_info = match_person(combined, tracked)

            if person_info:
                person_name = person_info["name"]
                role = person_info["role"]
                entity_id = person_info["entity_id"]
                influence = person_info["influence_weight"]
                matched += 1
            else:
                # For Ripple Insights, default to "Ripple" as speaker
                if article.get("source_label") == "Ripple Insights":
                    person_name = "Ripple (Corporate)"
                    role = "Corporate Statement"
                    entity_id = None
                    influence = 1.0
                else:
                    # Unknown speaker — still classify if relevant
                    person_name = article.get("source_label", "Unknown")
                    role = None
                    entity_id = None
                    influence = 0.5

            scores = classify_personnel_statement(
                article["source_title"], article.get("summary")
            )

            row = {
                "timestamp": article["timestamp"],
                "entity_id": entity_id,
                "person_name": person_name,
                "role": role,
                "statement_type": article.get("statement_type"),
                "source_title": article["source_title"],
                "source_url": article.get("source_url"),
                "cross_border_urgency": Decimal(str(scores["cross_border_urgency"])),
                "dlt_favorability": Decimal(str(scores["dlt_favorability"])),
                "stablecoin_stance": Decimal(str(scores["stablecoin_stance"])),
                "timeline_urgency": Decimal(str(scores["timeline_urgency"])),
                "xrp_mentioned": scores["xrp_mentioned"],
                "sentiment_score": Decimal(str(scores["sentiment_score"])),
                "influence_weight": Decimal(str(influence)),
            }

            stmt = pg_insert(XaiPersonnelIntelligence).values([row])
            stmt = stmt.on_conflict_do_update(
                constraint="uq_xai_personnel_person_source",
                set_={
                    "cross_border_urgency": stmt.excluded.cross_border_urgency,
                    "dlt_favorability": stmt.excluded.dlt_favorability,
                    "stablecoin_stance": stmt.excluded.stablecoin_stance,
                    "timeline_urgency": stmt.excluded.timeline_urgency,
                    "xrp_mentioned": stmt.excluded.xrp_mentioned,
                    "sentiment_score": stmt.excluded.sentiment_score,
                    "influence_weight": stmt.excluded.influence_weight,
                },
            )
            db.execute(stmt)
            classified += 1
        except Exception:
            db.rollback()
            logger.exception(
                "Error classifying personnel statement: %s",
                article.get("source_title", "")[:80],
            )

    db.commit()

    logger.info(
        "XAI personnel fetch: %d articles, %d classified, %d matched to tracked persons",
        len(all_articles), classified, matched,
    )

    return {
        "total": len(all_articles),
        "classified": classified,
        "matched_persons": matched,
    }
