"""Layer 5B: Real-time political news classifier.

Ingests news from RSS feeds and APIs, classifies via Claude API,
enriches with gematria, and tracks amplification/impact.
Delegates to political_news_service.
"""


class PoliticalNewsClassifier:
    """Classify political news articles for crypto market impact."""

    def classify_article(self, headline: str, summary: str) -> dict:
        from app.services.political_news_service import classify_article
        return classify_article(headline, summary)

    def compute_news_score(self, db, hours_window: int = 24) -> float:
        from app.services.political_news_service import compute_news_score
        return compute_news_score(db, hours_window)
