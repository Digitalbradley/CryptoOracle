"""XAI Phase B: Policy pipeline scraper + Claude classification.

Data sources (all free, no API keys):
1. BIS CPMI publications (HTML scrape)
2. FSB publications (HTML scrape)
3. SEC EDGAR XRP ETF filings search
4. Ripple Insights RSS (partnership news detection)

Classification via Claude Haiku when Anthropic key is available,
with keyword-based fallback otherwise.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.xai import XaiPartnership, XaiPolicyEvent

logger = logging.getLogger(__name__)

TIMEOUT = 20
HEADERS = {
    "User-Agent": "CryptoOracle/1.0 (Policy Research Bot)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# XRP-relevant keywords for filtering
XRP_POLICY_KEYWORDS = re.compile(
    r"(?i)\b("
    r"cross.?border|payment|stablecoin|cbdc|digital.?currency|"
    r"dlt|distributed.?ledger|blockchain|crypto.?asset|"
    r"tokeniz|ripple|xrp|rlusd|iso.?20022|"
    r"swift|correspondent.?bank|remittance|"
    r"etf|exchange.?traded|"
    r"fsb|cpmi|bis|basel|"
    r"regulatory.?framework|prudential|"
    r"money.?market|settlement|clearing"
    r")\b"
)


# ---------------------------------------------------------------------------
# Data source fetchers
# ---------------------------------------------------------------------------

def fetch_bis_cpmi() -> list[dict]:
    """Scrape BIS CPMI publications page for recent papers."""
    articles = []
    try:
        resp = httpx.get(
            "https://www.bis.org/cpmi/publ/index.htm",
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text

        # Parse publication entries — BIS uses a simple list structure
        # Look for title links and dates
        pattern = re.compile(
            r'<a\s+href="(/cpmi/publ/d\d+\.htm)"[^>]*>(.*?)</a>.*?'
            r'(\d{1,2}\s+\w+\s+\d{4})',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            url_path, title, date_str = match.groups()
            title = re.sub(r"<[^>]+>", "", title).strip()
            if not title:
                continue

            # Filter for XRP-relevant content
            if not XRP_POLICY_KEYWORDS.search(title):
                continue

            try:
                ts = datetime.strptime(date_str.strip(), "%d %B %Y").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source": "BIS CPMI",
                "event_type": "publication",
                "title": title[:500],
                "url": f"https://www.bis.org{url_path}",
                "summary": None,
            })

        logger.info("BIS CPMI: found %d relevant publications", len(articles))
    except Exception:
        logger.exception("Error scraping BIS CPMI")

    return articles


def fetch_fsb_publications() -> list[dict]:
    """Scrape FSB publications for cross-border payments and crypto policy."""
    articles = []
    try:
        resp = httpx.get(
            "https://www.fsb.org/publications/",
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text

        # FSB publication list items — title + date
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

            if not XRP_POLICY_KEYWORDS.search(title):
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
                "source": "FSB",
                "event_type": "publication",
                "title": title[:500],
                "url": url,
                "summary": None,
            })

        logger.info("FSB: found %d relevant publications", len(articles))
    except Exception:
        logger.exception("Error scraping FSB publications")

    return articles


def fetch_sec_edgar_xrp() -> list[dict]:
    """Search SEC EDGAR for XRP ETF filings."""
    articles = []
    try:
        # EDGAR full-text search API
        resp = httpx.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={
                "q": '"XRP" OR "Ripple"',
                "dateRange": "custom",
                "startdt": (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
                    "%Y-%m-%d"
                ),
                "enddt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "forms": "S-1,19b-4,8-A12B",
            },
            headers={
                "User-Agent": "CryptoOracle research@example.com",
                "Accept": "application/json",
            },
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()

        for hit in data.get("hits", {}).get("hits", [])[:10]:
            source = hit.get("_source", {})
            title = source.get("file_description") or source.get("display_names", [""])[0]
            filed = source.get("file_date", "")

            if not title:
                continue

            try:
                ts = datetime.strptime(filed, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                ts = datetime.now(timezone.utc)

            filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=xrp&type=&dateb=&owner=include&count=10"

            articles.append({
                "timestamp": ts,
                "source": "SEC EDGAR",
                "event_type": "etf_filing",
                "title": title[:500],
                "url": filing_url,
                "summary": None,
            })

        logger.info("SEC EDGAR: found %d XRP-related filings", len(articles))
    except Exception:
        logger.debug("SEC EDGAR search unavailable (non-critical)")

    return articles


def fetch_ripple_insights() -> list[dict]:
    """Fetch Ripple Insights blog/newsroom for partnership announcements."""
    articles = []
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed — Ripple Insights fetch skipped")
        return []

    try:
        feed = feedparser.parse("https://ripple.com/insights/feed/")
        for entry in feed.entries[:15]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}"

            # Filter for partnership/adoption relevant content
            if not XRP_POLICY_KEYWORDS.search(text):
                continue

            published = entry.get("published_parsed")
            if published:
                from time import mktime
                ts = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source": "Ripple Insights",
                "event_type": "announcement",
                "title": title[:500],
                "url": entry.get("link", ""),
                "summary": summary[:2000] if summary else None,
            })

        logger.info("Ripple Insights: found %d relevant articles", len(articles))
    except Exception:
        logger.exception("Error fetching Ripple Insights RSS")

    return articles


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Keyword-based scoring (fallback)
_FAVORABLE_KEYWORDS = re.compile(
    r"(?i)\b(adopt|embrace|framework|clarity|approve|enable|"
    r"support|innovation|pilot|launch|partner|interoperab|"
    r"iso.?20022|real.?time|instant|efficient)\b"
)
_UNFAVORABLE_KEYWORDS = re.compile(
    r"(?i)\b(ban|restrict|prohibit|crack.?down|enforce|"
    r"concern|risk|warn|delay|reject|oppose|threat|"
    r"sanction|fine|penalty|lawsuit)\b"
)
_XRP_KEYWORDS = re.compile(
    r"(?i)\b(xrp|ripple|rlusd|xrpl|odl|on.?demand.?liquidity)\b"
)


def _keyword_classify_policy(title: str, summary: str | None = None) -> dict:
    """Keyword-based policy classification (fallback)."""
    text = f"{title} {summary or ''}"

    # Cross-border relevance
    cb_matches = len(re.findall(
        r"(?i)\b(cross.?border|payment|remittance|settlement|correspondent|swift)\b",
        text,
    ))
    cross_border = min(1.0, cb_matches * 0.2)

    # DLT favorability
    fav = len(_FAVORABLE_KEYWORDS.findall(text))
    unfav = len(_UNFAVORABLE_KEYWORDS.findall(text))
    total = fav + unfav
    dlt_fav = ((fav - unfav) / total) if total > 0 else 0.0

    # Stablecoin stance
    sc_matches = len(re.findall(r"(?i)\b(stablecoin|cbdc|rlusd|digital.?dollar)\b", text))
    stablecoin = min(1.0, sc_matches * 0.25) * (1.0 if fav >= unfav else -1.0)

    # Regulatory direction
    reg_dir = dlt_fav * 0.8  # approximation

    # Timeline urgency
    urgency_words = len(re.findall(
        r"(?i)\b(imminent|immediate|final|enacted|effective|deadline|Q[1-4]|2026|2025)\b",
        text,
    ))
    timeline = min(1.0, urgency_words * 0.25)

    # XRP mentioned
    xrp_mentioned = bool(_XRP_KEYWORDS.search(text))

    # Composite impact
    impact = (
        cross_border * 0.25
        + dlt_fav * 0.25
        + stablecoin * 0.20
        + reg_dir * 0.15
        + timeline * 0.15
    )
    if xrp_mentioned:
        impact = impact * 1.3  # 30% boost for direct mention

    return {
        "cross_border_relevance": round(cross_border, 2),
        "dlt_favorability": round(dlt_fav, 2),
        "stablecoin_stance": round(stablecoin, 2),
        "regulatory_direction": round(reg_dir, 2),
        "timeline_urgency": round(timeline, 2),
        "xrp_mentioned": xrp_mentioned,
        "policy_impact_score": round(max(-1.0, min(1.0, impact)), 2),
    }


def classify_policy_event(title: str, summary: str | None = None) -> dict:
    """Classify a policy event for XRP adoption impact.

    Uses Claude Haiku if available, falls back to keyword classification.
    """
    if not settings.anthropic_api_key:
        return _keyword_classify_policy(title, summary)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        prompt = (
            "Classify this regulatory/policy event for its impact on XRP/Ripple "
            "institutional adoption.\n\n"
            f"Title: {title}\n"
            f"Summary: {summary or 'N/A'}\n\n"
            "Respond with ONLY a JSON object (no markdown):\n"
            '{"cross_border_relevance": <0.0-1.0, relevance to cross-border payments>, '
            '"dlt_favorability": <-1.0 to 1.0, favorable=positive for DLT adoption>, '
            '"stablecoin_stance": <-1.0 to 1.0, favorable=positive for stablecoins>, '
            '"regulatory_direction": <-1.0 to 1.0, positive=enabling regulation>, '
            '"timeline_urgency": <0.0-1.0, how soon this impacts markets>, '
            '"xrp_mentioned": <true/false, XRP/Ripple/RLUSD directly mentioned>, '
            '"policy_impact_score": <-1.0 to 1.0, overall impact on XRP adoption>}'
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
            "cross_border_relevance": float(result.get("cross_border_relevance", 0.5)),
            "dlt_favorability": float(result.get("dlt_favorability", 0.0)),
            "stablecoin_stance": float(result.get("stablecoin_stance", 0.0)),
            "regulatory_direction": float(result.get("regulatory_direction", 0.0)),
            "timeline_urgency": float(result.get("timeline_urgency", 0.3)),
            "xrp_mentioned": bool(result.get("xrp_mentioned", False)),
            "policy_impact_score": float(result.get("policy_impact_score", 0.0)),
        }
    except Exception:
        logger.exception("Claude policy classification failed, using keyword fallback")
        return _keyword_classify_policy(title, summary)


# ---------------------------------------------------------------------------
# Partnership detection from Ripple Insights
# ---------------------------------------------------------------------------

_PARTNERSHIP_PATTERN = re.compile(
    r"(?i)\b(partner|agreement|collab|join|integrat|adopt|deploy|"
    r"sign|mou|memorandum|pilot|launch.*with)\b"
)


def detect_new_partnerships(articles: list[dict], db: Session) -> int:
    """Check Ripple Insights articles for new partnership announcements.

    Creates 'announced' stage entries in xai_partnerships for new detections.
    Returns count of new partnerships added.
    """
    count = 0
    for article in articles:
        if article["source"] != "Ripple Insights":
            continue
        text = f"{article['title']} {article.get('summary', '')}"
        if not _PARTNERSHIP_PATTERN.search(text):
            continue

        # Extract potential partner name (simple heuristic)
        # Look for "with [Company Name]" or "[Company] partners"
        partner_match = re.search(
            r"(?i)(?:with|and|partners?\s+with)\s+([A-Z][A-Za-z\s&]+?)(?:\s+(?:to|for|in|on|,|\.))",
            text,
        )
        if not partner_match:
            continue

        partner_name = partner_match.group(1).strip()
        if len(partner_name) < 3 or len(partner_name) > 100:
            continue

        # Check if already exists
        from sqlalchemy import select, func
        exists = db.execute(
            select(func.count()).select_from(XaiPartnership)
            .where(func.lower(XaiPartnership.partner_name) == partner_name.lower())
        ).scalar()

        if exists:
            continue

        # Insert new partnership as announced
        new_p = XaiPartnership(
            partner_name=partner_name,
            partner_type="unknown",
            partnership_type="ripplenet",
            pipeline_stage="announced",
            stage_score=Decimal("0.15"),
            partner_weight=Decimal("1.0"),
            source_url=article.get("url"),
            notes=f"Auto-detected from: {article['title'][:200]}",
        )
        db.add(new_p)
        count += 1
        logger.info("New partnership detected: %s", partner_name)

    if count > 0:
        db.commit()
    return count


# ---------------------------------------------------------------------------
# Main fetch + classify + store
# ---------------------------------------------------------------------------

def fetch_and_classify(db: Session) -> dict:
    """Fetch policy events from all sources, classify, and store.

    Returns summary dict with counts per source.
    """
    all_articles: list[dict] = []

    # Fetch from all sources
    all_articles.extend(fetch_bis_cpmi())
    all_articles.extend(fetch_fsb_publications())
    all_articles.extend(fetch_sec_edgar_xrp())

    ripple_articles = fetch_ripple_insights()
    all_articles.extend(ripple_articles)

    if not all_articles:
        logger.info("No XAI policy articles found from any source")
        return {"total": 0, "classified": 0, "partnerships_detected": 0}

    # Classify and store
    classified = 0
    for article in all_articles:
        try:
            scores = classify_policy_event(
                article["title"], article.get("summary")
            )

            row = {
                "timestamp": article["timestamp"],
                "source": article["source"],
                "event_type": article.get("event_type"),
                "title": article["title"],
                "summary": article.get("summary"),
                "url": article.get("url"),
                "cross_border_relevance": Decimal(str(scores["cross_border_relevance"])),
                "dlt_favorability": Decimal(str(scores["dlt_favorability"])),
                "stablecoin_stance": Decimal(str(scores["stablecoin_stance"])),
                "regulatory_direction": Decimal(str(scores["regulatory_direction"])),
                "timeline_urgency": Decimal(str(scores["timeline_urgency"])),
                "xrp_mentioned": scores["xrp_mentioned"],
                "policy_impact_score": Decimal(str(scores["policy_impact_score"])),
            }

            stmt = pg_insert(XaiPolicyEvent).values([row])
            stmt = stmt.on_conflict_do_update(
                constraint="uq_xai_policy_source_title",
                set_={
                    "cross_border_relevance": stmt.excluded.cross_border_relevance,
                    "dlt_favorability": stmt.excluded.dlt_favorability,
                    "stablecoin_stance": stmt.excluded.stablecoin_stance,
                    "regulatory_direction": stmt.excluded.regulatory_direction,
                    "timeline_urgency": stmt.excluded.timeline_urgency,
                    "xrp_mentioned": stmt.excluded.xrp_mentioned,
                    "policy_impact_score": stmt.excluded.policy_impact_score,
                },
            )
            db.execute(stmt)
            classified += 1
        except Exception:
            db.rollback()
            logger.exception(
                "Error classifying policy event: %s",
                article.get("title", "")[:80],
            )

    db.commit()

    # Detect new partnerships from Ripple Insights
    partnerships = detect_new_partnerships(ripple_articles, db)

    logger.info(
        "XAI policy fetch: %d articles, %d classified, %d partnerships detected",
        len(all_articles), classified, partnerships,
    )

    return {
        "total": len(all_articles),
        "classified": classified,
        "partnerships_detected": partnerships,
    }
