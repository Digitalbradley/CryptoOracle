"""Political news service — multi-source news fetcher with classification.

Data sources (each independent, API key gated):
1. RSS feeds (always free — CoinDesk, CoinTelegraph, The Block)
2. NewsAPI (gated behind settings.newsapi_key)
3. GNews (gated behind settings.gnews_api_key)

Classification via Claude API (gated behind settings.anthropic_api_key)
with keyword-based fallback when no API key is configured.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import settings
from app.models.political_news import PoliticalNews

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RSS feed URLs (free, no API key)
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
    {"url": "https://cointelegraph.com/rss", "name": "CoinTelegraph"},
    {"url": "https://www.theblock.co/rss.xml", "name": "The Block"},
]

# Political/regulatory keywords for filtering RSS articles
POLITICAL_KEYWORDS = re.compile(
    r"(?i)\b("
    r"regulation|regulatory|sec|cftc|congress|senate|legislation|bill|law|"
    r"ban|sanction|tax|treasury|fed|fomc|interest rate|inflation|cpi|"
    r"biden|trump|white house|executive order|policy|tariff|"
    r"central bank|cbdc|stablecoin|crypto bill|enforcement|crackdown|"
    r"etf|spot etf|approval|reject|compliance|aml|kyc|"
    r"china|eu|europe|mika|mica|japan|korea|india|russia|"
    r"election|vote|debate|campaign|political|geopolitic"
    r")\b"
)

# ---------------------------------------------------------------------------
# Keyword-based classification (fallback when no Claude API key)
# ---------------------------------------------------------------------------

_CATEGORY_PATTERNS = {
    "monetary_policy": re.compile(
        r"(?i)\b(fed|fomc|interest rate|inflation|cpi|gdp|central bank|"
        r"rate hike|rate cut|quantitative|treasury|yields?|bonds?)\b"
    ),
    "crypto_regulation": re.compile(
        r"(?i)\b(sec|cftc|regulation|regulatory|compliance|enforcement|"
        r"crypto bill|stablecoin|cbdc|etf|spot etf|aml|kyc|mika|mica)\b"
    ),
    "fiscal_policy": re.compile(
        r"(?i)\b(tax|tariff|spending|deficit|debt ceiling|budget|"
        r"stimulus|bailout|infrastructure)\b"
    ),
    "geopolitical": re.compile(
        r"(?i)\b(sanction|war|conflict|trade war|china|russia|"
        r"geopolitic|nato|opec|oil|embargo)\b"
    ),
    "election": re.compile(
        r"(?i)\b(election|vote|debate|campaign|midterm|primary|"
        r"democrat|republican|poll|ballot)\b"
    ),
}

_POSITIVE_WORDS = re.compile(
    r"(?i)\b(approve|approval|bullish|adopt|embrace|support|positive|"
    r"rally|surge|gain|up|growth|optimis|favorable|clarity)\b"
)
_NEGATIVE_WORDS = re.compile(
    r"(?i)\b(ban|reject|crash|bearish|crack ?down|enforce|sue|lawsuit|"
    r"fine|penalty|risk|fear|concern|warn|drop|fall|negative|uncertainty)\b"
)


def _keyword_classify(headline: str, summary: str | None = None) -> dict:
    """Keyword-based article classification (fallback)."""
    text = f"{headline} {summary or ''}"

    # Detect category
    category = "general"
    subcategory = None
    for cat, pattern in _CATEGORY_PATTERNS.items():
        if pattern.search(text):
            category = cat
            # Extract first matching keyword as subcategory
            match = pattern.search(text)
            if match:
                subcategory = match.group(0).lower()
            break

    # Crypto relevance: count political keyword matches
    keyword_matches = len(POLITICAL_KEYWORDS.findall(text))
    crypto_relevance = min(1.0, keyword_matches * 0.15)

    # Simple sentiment scoring
    pos_count = len(_POSITIVE_WORDS.findall(text))
    neg_count = len(_NEGATIVE_WORDS.findall(text))
    total = pos_count + neg_count
    if total > 0:
        sentiment = (pos_count - neg_count) / total
    else:
        sentiment = 0.0

    # Urgency: based on strong language
    urgency_words = len(re.findall(
        r"(?i)\b(breaking|urgent|emergency|immediately|crisis|crash|alert)\b",
        text,
    ))
    urgency = min(1.0, urgency_words * 0.3)

    return {
        "category": category,
        "subcategory": subcategory,
        "crypto_relevance_score": round(crypto_relevance, 4),
        "sentiment_score": round(sentiment, 4),
        "urgency_score": round(urgency, 4),
        "entities": [],
    }


def classify_article(headline: str, summary: str | None = None) -> dict:
    """Classify a news article for crypto market impact.

    Uses Claude API if available, otherwise falls back to keyword classification.
    """
    if not settings.anthropic_api_key:
        return _keyword_classify(headline, summary)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        prompt = (
            f"Classify this news article for cryptocurrency market impact.\n\n"
            f"Headline: {headline}\n"
            f"Summary: {summary or 'N/A'}\n\n"
            f"Respond with ONLY a JSON object (no markdown):\n"
            f'{{"category": "<monetary_policy|crypto_regulation|fiscal_policy|'
            f'geopolitical|election|general>", '
            f'"subcategory": "<specific topic>", '
            f'"crypto_relevance_score": <0.0-1.0>, '
            f'"sentiment_score": <-1.0 to 1.0, positive=bullish for crypto>, '
            f'"urgency_score": <0.0-1.0>, '
            f'"entities": ["<key people/orgs mentioned>"]}}'
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        text = response.content[0].text.strip()
        # Strip markdown code block if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)

        # Ensure required fields
        return {
            "category": result.get("category", "general"),
            "subcategory": result.get("subcategory"),
            "crypto_relevance_score": float(result.get("crypto_relevance_score", 0.5)),
            "sentiment_score": float(result.get("sentiment_score", 0.0)),
            "urgency_score": float(result.get("urgency_score", 0.0)),
            "entities": result.get("entities", []),
        }
    except Exception:
        logger.exception("Claude classification failed, using keyword fallback")
        return _keyword_classify(headline, summary)


def enrich_with_gematria(headline: str) -> dict:
    """Compute gematria values for a headline."""
    from app.services.numerology_compute import GematriaCalculator

    calc = GematriaCalculator()
    return calc.calculate_all_ciphers(headline)


# ---------------------------------------------------------------------------
# Data source fetchers
# ---------------------------------------------------------------------------

def fetch_rss_news() -> list[dict]:
    """Fetch political news from RSS feeds (always available)."""
    articles = []

    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed — RSS fetch skipped")
        return []

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:20]:  # Last 20 entries per feed
                title = entry.get("title", "")
                summary = entry.get("summary", "")

                # Filter: only keep articles matching political keywords
                if not POLITICAL_KEYWORDS.search(f"{title} {summary}"):
                    continue

                # Parse publication date
                published = entry.get("published_parsed")
                if published:
                    from time import mktime
                    ts = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
                else:
                    ts = datetime.now(timezone.utc)

                articles.append({
                    "timestamp": ts,
                    "source_name": feed_info["name"],
                    "headline": title[:500],
                    "source_url": entry.get("link", ""),
                    "summary": summary[:2000] if summary else None,
                })
        except Exception:
            logger.exception("Error fetching RSS from %s", feed_info["name"])

    return articles


def fetch_newsapi(query: str = "cryptocurrency regulation", hours_back: int = 4) -> list[dict] | None:
    """Fetch news from NewsAPI (gated behind newsapi_key)."""
    if not settings.newsapi_key:
        return None

    try:
        from_dt = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
        resp = httpx.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": from_dt,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 20,
                "apiKey": settings.newsapi_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for art in data.get("articles", []):
            ts_str = art.get("publishedAt", "")
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source_name": art.get("source", {}).get("name", "NewsAPI"),
                "headline": (art.get("title") or "")[:500],
                "source_url": art.get("url", ""),
                "summary": (art.get("description") or "")[:2000],
            })
        return articles
    except Exception:
        logger.exception("Error fetching from NewsAPI")
        return None


def fetch_gnews(query: str = "cryptocurrency policy", hours_back: int = 4) -> list[dict] | None:
    """Fetch news from GNews API (gated behind gnews_api_key)."""
    if not settings.gnews_api_key:
        return None

    try:
        from_dt = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        resp = httpx.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "from": from_dt,
                "lang": "en",
                "max": 20,
                "token": settings.gnews_api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for art in data.get("articles", []):
            ts_str = art.get("publishedAt", "")
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                ts = datetime.now(timezone.utc)

            articles.append({
                "timestamp": ts,
                "source_name": art.get("source", {}).get("name", "GNews"),
                "headline": (art.get("title") or "")[:500],
                "source_url": art.get("url", ""),
                "summary": (art.get("description") or "")[:2000],
            })
        return articles
    except Exception:
        logger.exception("Error fetching from GNews")
        return None


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def compute_news_score(db: Session, hours_window: int = 24) -> float:
    """Compute weighted news sentiment score from recent articles.

    Weighted average of sentiment_score, weighted by crypto_relevance * urgency.
    Returns 0.0 if no relevant articles.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_window)

    rows = db.execute(
        select(PoliticalNews)
        .where(
            PoliticalNews.timestamp >= cutoff,
            PoliticalNews.crypto_relevance_score.isnot(None),
            PoliticalNews.sentiment_score.isnot(None),
        )
        .order_by(PoliticalNews.timestamp.desc())
    ).scalars().all()

    if not rows:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for r in rows:
        relevance = float(r.crypto_relevance_score or 0)
        urgency = float(r.urgency_score or 0.5)
        sentiment = float(r.sentiment_score or 0)

        weight = relevance * (0.5 + urgency)  # urgency boosts weight
        weighted_sum += sentiment * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(max(-1.0, min(1.0, weighted_sum / total_weight)), 4)


# ---------------------------------------------------------------------------
# Fetch + classify + store
# ---------------------------------------------------------------------------

def fetch_and_store(db: Session, *, commit: bool = True) -> int:
    """Fetch news from all available sources, classify, enrich, and store.

    Returns number of articles processed.
    """
    all_articles = []

    # RSS (always available)
    rss_articles = fetch_rss_news()
    all_articles.extend(rss_articles)
    logger.info("RSS: fetched %d articles", len(rss_articles))

    # NewsAPI (key gated)
    newsapi_articles = fetch_newsapi()
    if newsapi_articles:
        all_articles.extend(newsapi_articles)
        logger.info("NewsAPI: fetched %d articles", len(newsapi_articles))

    # GNews (key gated)
    gnews_articles = fetch_gnews()
    if gnews_articles:
        all_articles.extend(gnews_articles)
        logger.info("GNews: fetched %d articles", len(gnews_articles))

    if not all_articles:
        logger.info("No political news articles found")
        return 0

    count = 0
    for article in all_articles:
        try:
            # Classify
            classification = classify_article(
                article["headline"], article.get("summary")
            )

            # Gematria enrichment
            headline_gematria = enrich_with_gematria(article["headline"])

            row = {
                "timestamp": article["timestamp"],
                "source_name": article["source_name"],
                "headline": article["headline"],
                "source_url": article.get("source_url"),
                "summary": article.get("summary"),
                "category": classification["category"],
                "subcategory": classification.get("subcategory"),
                "crypto_relevance_score": Decimal(
                    str(classification["crypto_relevance_score"])
                ),
                "sentiment_score": Decimal(
                    str(classification["sentiment_score"])
                ),
                "urgency_score": Decimal(
                    str(classification["urgency_score"])
                ),
                "entities": classification.get("entities"),
                "headline_gematria": headline_gematria,
            }

            stmt = pg_insert(PoliticalNews).values([row])
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp", "source_name", "headline"],
                set_={
                    "category": stmt.excluded.category,
                    "subcategory": stmt.excluded.subcategory,
                    "crypto_relevance_score": stmt.excluded.crypto_relevance_score,
                    "sentiment_score": stmt.excluded.sentiment_score,
                    "urgency_score": stmt.excluded.urgency_score,
                    "entities": stmt.excluded.entities,
                    "headline_gematria": stmt.excluded.headline_gematria,
                },
            )
            db.execute(stmt)
            count += 1
        except Exception:
            db.rollback()
            logger.exception("Error processing article: %s", article.get("headline", "")[:80])

    if commit:
        db.commit()
    logger.info("Stored %d political news articles", count)
    return count


def is_any_source_available() -> bool:
    """Check if any news source beyond RSS is configured."""
    return bool(settings.newsapi_key or settings.gnews_api_key)
