"""Political narrative service — detects persistent political/macro narratives.

Clusters recent classified news articles by category to identify dominant
narratives that persist over hours/days. Outputs narrative_score for the
political signal composite.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.political_news import PoliticalNews

logger = logging.getLogger(__name__)


def detect_narratives(db: Session, hours_lookback: int = 72) -> list[dict]:
    """Detect active political/macro narratives from recent news.

    Groups articles by category, computes article count, average sentiment,
    velocity (articles/hour), and strength.

    Returns list sorted by strength descending.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)

    rows = db.execute(
        select(PoliticalNews)
        .where(
            PoliticalNews.timestamp >= cutoff,
            PoliticalNews.crypto_relevance_score >= Decimal("0.3"),
        )
        .order_by(PoliticalNews.timestamp.desc())
    ).scalars().all()

    if not rows:
        return []

    # Group by category
    clusters: dict[str, list] = defaultdict(list)
    for r in rows:
        key = r.category or "general"
        if r.subcategory:
            key = f"{key}/{r.subcategory}"
        clusters[key].append(r)

    narratives = []
    for narrative_name, articles in clusters.items():
        if len(articles) < 2:
            continue  # Need at least 2 articles to form a narrative

        sentiments = [
            float(a.sentiment_score) for a in articles
            if a.sentiment_score is not None
        ]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        # Velocity: articles per hour
        if hours_lookback > 0:
            velocity = len(articles) / hours_lookback
        else:
            velocity = float(len(articles))

        # Direction
        if avg_sentiment > 0.15:
            direction = "bullish"
        elif avg_sentiment < -0.15:
            direction = "bearish"
        else:
            direction = "neutral"

        # Strength: volume * sentiment magnitude * velocity
        strength = len(articles) * abs(avg_sentiment) * (1.0 + velocity)

        narratives.append({
            "narrative": narrative_name,
            "article_count": len(articles),
            "avg_sentiment": round(avg_sentiment, 4),
            "velocity": round(velocity, 4),
            "direction": direction,
            "strength": round(strength, 4),
        })

    # Sort by strength descending
    narratives.sort(key=lambda x: x["strength"], reverse=True)
    return narratives


def get_dominant_narrative(db: Session) -> dict | None:
    """Get the strongest active narrative.

    Returns the narrative with highest strength, or None if no narratives.
    """
    narratives = detect_narratives(db)
    if not narratives:
        return None

    top = narratives[0]
    return {
        "narrative": top["narrative"],
        "strength": top["strength"],
        "direction": top["direction"],
        "article_count": top["article_count"],
        "avg_sentiment": top["avg_sentiment"],
    }


def compute_narrative_score(db: Session) -> float:
    """Compute narrative score for the political signal composite.

    Score = strength * direction_multiplier, clamped to [-1.0, +1.0].
    Returns 0.0 if no active narratives.
    """
    dominant = get_dominant_narrative(db)
    if not dominant:
        return 0.0

    direction_map = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}
    direction_mult = direction_map.get(dominant["direction"], 0.0)

    # Normalize strength to [-1, 1] range
    # Typical strength values: 0-10 for moderate, 10+ for strong
    normalized_strength = min(1.0, dominant["strength"] / 5.0)

    score = normalized_strength * direction_mult
    return round(max(-1.0, min(1.0, score)), 4)


# Need Decimal for the query filter
from decimal import Decimal
