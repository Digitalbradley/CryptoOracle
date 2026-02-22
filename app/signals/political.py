"""Layer 5: Political events and macro intelligence composite engine.

Combines calendar proximity, news sentiment, and narrative detection
into a composite political_score in range -1.0 to +1.0.
"""


def compute_political_score(
    calendar_proximity_score: float,
    news_sentiment_score: float,
    narrative_score: float,
) -> float:
    """Compute composite political score from sub-module scores.

    Formula:
        0.30 * calendar_proximity_score +
        0.35 * news_sentiment_score +
        0.35 * narrative_score

    Special overrides for black swan events are handled in
    political_signal_service.compute_political_signal().
    """
    score = (
        0.30 * calendar_proximity_score
        + 0.35 * news_sentiment_score
        + 0.35 * narrative_score
    )
    return max(-1.0, min(1.0, score))
