"""Confluence scoring engine — weighted composite of all 7 signal layers.

Gathers latest scores from TA, celestial, numerology, sentiment, on-chain,
political, and macro liquidity layers. Computes a weighted composite score,
determines signal strength, and detects layer alignment.

Missing layers (None scores) are handled gracefully — their weight is
redistributed proportionally across available layers.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.celestial_state import CelestialState
from app.models.confluence_scores import ConfluenceScores
from app.models.macro_liquidity import MacroLiquiditySignal
from app.models.numerology_daily import NumerologyDaily
from app.models.onchain_metrics import OnchainMetrics
from app.models.political_signal import PoliticalSignal
from app.models.sentiment_data import SentimentData
from app.models.signal_weights import SignalWeights
from app.models.ta_indicators import TAIndicators
from app.signals.celestial import CelestialEngine
from app.signals.numerology import compute_daily_numerology
from app.services.sentiment_fetch import fetch_and_store_current

logger = logging.getLogger(__name__)

# Default weights (must sum to 1.0) — brief Section 7.1
DEFAULT_WEIGHTS = {
    "ta": 0.20,
    "onchain": 0.15,
    "celestial": 0.12,
    "numerology": 0.08,
    "sentiment": 0.12,
    "political": 0.13,
    "macro": 0.20,
}

# Signal strength thresholds
STRENGTH_THRESHOLDS = [
    (0.6, "strong_buy"),
    (0.2, "buy"),
    (-0.2, "neutral"),
    (-0.6, "sell"),
]
# Anything below -0.6 is "strong_sell"


class ConfluenceEngine:
    """Weighted composite scorer combining all signal layers."""

    def get_active_weights(self, db: Session) -> dict:
        """Load the active weight profile from signal_weights table.

        Falls back to DEFAULT_WEIGHTS if no active profile exists.
        """
        row = db.execute(
            select(SignalWeights).where(SignalWeights.is_active.is_(True))
        ).scalar_one_or_none()

        if row is None:
            return dict(DEFAULT_WEIGHTS)

        return {
            "ta": float(row.ta_weight),
            "onchain": float(row.onchain_weight),
            "celestial": float(row.celestial_weight),
            "numerology": float(row.numerology_weight),
            "sentiment": float(row.sentiment_weight),
            "political": float(row.political_weight),
            "macro": float(row.macro_weight),
        }

    def gather_latest_scores(
        self, db: Session, symbol: str, timeframe: str
    ) -> dict:
        """Query the latest score from each signal layer.

        Returns:
            Dict with keys: ta_score, celestial_score, numerology_score,
            sentiment_score, onchain_score, political_score.
            Values are float or None if no data available.
        """
        scores = {}

        # TA: latest for symbol + timeframe
        ta_row = db.execute(
            select(TAIndicators)
            .where(
                TAIndicators.symbol == symbol,
                TAIndicators.timeframe == timeframe,
            )
            .order_by(TAIndicators.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        scores["ta_score"] = float(ta_row.ta_score) if ta_row and ta_row.ta_score else None

        # Celestial: today — compute on-the-fly if not in DB
        today = date.today()
        today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        cel_row = db.execute(
            select(CelestialState)
            .where(CelestialState.timestamp == today_start)
        ).scalar_one_or_none()
        if cel_row and cel_row.celestial_score is not None:
            scores["celestial_score"] = float(cel_row.celestial_score)
        else:
            try:
                engine = CelestialEngine()
                state = engine.compute_daily_state(today, db)
                cel_val = state.get("celestial_score") if isinstance(state, dict) else getattr(state, "celestial_score", None)
                scores["celestial_score"] = float(cel_val) if cel_val is not None else None
            except Exception:
                logger.debug("Celestial on-the-fly computation failed")
                scores["celestial_score"] = None

        # Numerology: today — compute on-the-fly if not in DB
        num_row = db.execute(
            select(NumerologyDaily).where(NumerologyDaily.date == today)
        ).scalar_one_or_none()
        if num_row and num_row.numerology_score is not None:
            scores["numerology_score"] = float(num_row.numerology_score)
        else:
            try:
                num_result = compute_daily_numerology(today, db)
                num_val = num_result.get("numerology_score") if isinstance(num_result, dict) else getattr(num_result, "numerology_score", None)
                scores["numerology_score"] = float(num_val) if num_val is not None else None
            except Exception:
                logger.debug("Numerology on-the-fly computation failed")
                scores["numerology_score"] = None

        # Sentiment: latest for symbol — fetch on-the-fly if not in DB
        sent_row = db.execute(
            select(SentimentData)
            .where(SentimentData.symbol == symbol)
            .order_by(SentimentData.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        if sent_row and sent_row.sentiment_score is not None:
            scores["sentiment_score"] = float(sent_row.sentiment_score)
        else:
            try:
                fetch_and_store_current(db, [symbol])
                sent_row = db.execute(
                    select(SentimentData)
                    .where(SentimentData.symbol == symbol)
                    .order_by(SentimentData.timestamp.desc())
                    .limit(1)
                ).scalar_one_or_none()
                scores["sentiment_score"] = float(sent_row.sentiment_score) if sent_row and sent_row.sentiment_score is not None else None
            except Exception:
                logger.debug("Sentiment on-the-fly fetch failed")
                scores["sentiment_score"] = None

        # On-chain: latest for symbol
        oc_row = db.execute(
            select(OnchainMetrics)
            .where(OnchainMetrics.symbol == symbol)
            .order_by(OnchainMetrics.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        scores["onchain_score"] = (
            float(oc_row.onchain_score) if oc_row and oc_row.onchain_score else None
        )

        # Political: latest (not symbol-specific)
        pol_row = db.execute(
            select(PoliticalSignal)
            .order_by(PoliticalSignal.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        scores["political_score"] = (
            float(pol_row.political_score) if pol_row and pol_row.political_score else None
        )

        # Macro liquidity: latest (not symbol-specific)
        macro_row = db.execute(
            select(MacroLiquiditySignal)
            .order_by(MacroLiquiditySignal.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        scores["macro_score"] = (
            float(macro_row.macro_score) if macro_row and macro_row.macro_score else None
        )

        return scores

    def compute_composite(self, scores: dict, weights: dict) -> dict:
        """Compute weighted composite score from individual layer scores.

        Missing (None) layers have their weight redistributed proportionally.

        Args:
            scores: {layer_score: float | None} for each layer
            weights: {layer: float} weight for each layer

        Returns:
            Full dict matching ConfluenceScores model columns
        """
        # Map score keys to weight keys
        score_to_weight = {
            "ta_score": "ta",
            "onchain_score": "onchain",
            "celestial_score": "celestial",
            "numerology_score": "numerology",
            "sentiment_score": "sentiment",
            "political_score": "political",
            "macro_score": "macro",
        }

        # Filter to available (non-None) layers
        available = {}
        for score_key, weight_key in score_to_weight.items():
            val = scores.get(score_key)
            if val is not None:
                available[score_key] = (val, weights.get(weight_key, 0))

        if not available:
            return self._empty_result(scores, weights)

        # Redistribute weights proportionally across available layers
        total_weight = sum(w for _, w in available.values())
        if total_weight == 0:
            return self._empty_result(scores, weights)

        # Compute weighted average
        composite = sum(
            val * (w / total_weight) for val, w in available.values()
        )
        composite = round(max(-1.0, min(1.0, composite)), 4)

        # Determine signal strength
        signal_strength = "strong_sell"
        for threshold, label in STRENGTH_THRESHOLDS:
            if composite >= threshold:
                signal_strength = label
                break

        # Detect alignment
        bullish = []
        bearish = []
        for score_key in score_to_weight:
            val = scores.get(score_key)
            if val is None:
                continue
            layer = score_to_weight[score_key]
            if val > 0.2:
                bullish.append(layer)
            elif val < -0.2:
                bearish.append(layer)

        # Aligned = whichever direction has more layers
        if len(bullish) >= len(bearish):
            aligned_layers = bullish
            alignment_direction = "bullish"
        else:
            aligned_layers = bearish
            alignment_direction = "bearish"

        return {
            "ta_score": scores.get("ta_score"),
            "onchain_score": scores.get("onchain_score"),
            "celestial_score": scores.get("celestial_score"),
            "numerology_score": scores.get("numerology_score"),
            "sentiment_score": scores.get("sentiment_score"),
            "political_score": scores.get("political_score"),
            "macro_score": scores.get("macro_score"),
            "weights": weights,
            "composite_score": composite,
            "signal_strength": signal_strength,
            "aligned_layers": {
                "direction": alignment_direction,
                "layers": aligned_layers,
            },
            "alignment_count": len(aligned_layers),
        }

    def compute_and_store(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        timestamp: datetime | None = None,
        *,
        commit: bool = True,
    ) -> dict:
        """Gather scores, compute composite, and store to database.

        Returns:
            Full confluence result dict
        """
        weights = self.get_active_weights(db)
        scores = self.gather_latest_scores(db, symbol, timeframe)
        result = self.compute_composite(scores, weights)

        ts = timestamp or datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )

        row = {
            "timestamp": ts,
            "symbol": symbol,
            "timeframe": timeframe,
            "ta_score": _to_decimal(result["ta_score"]),
            "onchain_score": _to_decimal(result["onchain_score"]),
            "celestial_score": _to_decimal(result["celestial_score"]),
            "numerology_score": _to_decimal(result["numerology_score"]),
            "sentiment_score": _to_decimal(result["sentiment_score"]),
            "political_score": _to_decimal(result["political_score"]),
            "macro_score": _to_decimal(result["macro_score"]),
            "weights": result["weights"],
            "composite_score": Decimal(str(result["composite_score"])),
            "signal_strength": result["signal_strength"],
            "aligned_layers": result["aligned_layers"],
            "alignment_count": result["alignment_count"],
        }

        stmt = pg_insert(ConfluenceScores).values([row])
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp", "symbol", "timeframe"],
            set_={
                "ta_score": stmt.excluded.ta_score,
                "onchain_score": stmt.excluded.onchain_score,
                "celestial_score": stmt.excluded.celestial_score,
                "numerology_score": stmt.excluded.numerology_score,
                "sentiment_score": stmt.excluded.sentiment_score,
                "political_score": stmt.excluded.political_score,
                "macro_score": stmt.excluded.macro_score,
                "weights": stmt.excluded.weights,
                "composite_score": stmt.excluded.composite_score,
                "signal_strength": stmt.excluded.signal_strength,
                "aligned_layers": stmt.excluded.aligned_layers,
                "alignment_count": stmt.excluded.alignment_count,
            },
        )
        db.execute(stmt)
        if commit:
            db.commit()

        logger.info(
            "Confluence %s %s: composite=%.4f (%s), aligned=%d",
            symbol,
            timeframe,
            result["composite_score"],
            result["signal_strength"],
            result["alignment_count"],
        )
        return result

    def _empty_result(self, scores: dict, weights: dict) -> dict:
        """Return a neutral result when no layers are available."""
        return {
            **scores,
            "weights": weights,
            "composite_score": 0.0,
            "signal_strength": "neutral",
            "aligned_layers": {"direction": "neutral", "layers": []},
            "alignment_count": 0,
        }


def _to_decimal(val) -> Decimal | None:
    if val is None:
        return None
    return Decimal(str(round(val, 4)))
