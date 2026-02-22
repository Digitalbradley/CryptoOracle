"""Backtesting engine — 47-day cycle validation + general signal backtester.

CycleBacktester: Statistical analysis of the 47-day crash cycle hypothesis.
Uses chi-squared test to determine if crash clustering at 47-day intervals
is statistically significant. Cross-references with celestial and numerological
state at each crash.

SignalBacktester: Replays historical data to measure signal accuracy and
optimize layer weights via grid search.
"""

import logging
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from itertools import product

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.celestial_state import CelestialState
from app.models.historical_events import HistoricalEvents
from app.models.numerology_daily import NumerologyDaily
from app.models.price_data import PriceData
from app.models.ta_indicators import TAIndicators
from app.models.sentiment_data import SentimentData
from app.services.confluence_engine import ConfluenceEngine

logger = logging.getLogger(__name__)


class CycleBacktester:
    """Statistical validation of the 47-day crash cycle hypothesis."""

    def get_crash_events(
        self,
        db: Session,
        symbol: str = "BTC/USDT",
        min_magnitude: float = -10.0,
    ) -> list[dict]:
        """Pull crash events from historical_events table.

        Args:
            symbol: Trading pair to analyze
            min_magnitude: Minimum magnitude (negative %). E.g. -10.0 means >= 10% drop.

        Returns:
            List of crash event dicts, sorted by timestamp ascending.
        """
        rows = db.execute(
            select(HistoricalEvents)
            .where(
                HistoricalEvents.symbol == symbol,
                HistoricalEvents.event_type == "crash",
                HistoricalEvents.magnitude_pct <= min_magnitude,
            )
            .order_by(HistoricalEvents.timestamp.asc())
        ).scalars().all()

        return [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "date": r.timestamp.date(),
                "symbol": r.symbol,
                "magnitude_pct": float(r.magnitude_pct) if r.magnitude_pct else None,
                "price_at_event": float(r.price_at_event) if r.price_at_event else None,
                "lunar_phase_name": r.lunar_phase_name,
                "mercury_retrograde": r.mercury_retrograde,
                "date_universal_number": r.date_universal_number,
            }
            for r in rows
        ]

    def compute_intervals(self, events: list[dict]) -> list[int]:
        """Compute day-count intervals between consecutive crashes.

        Returns:
            List of integer day intervals.
        """
        if len(events) < 2:
            return []

        intervals = []
        for i in range(1, len(events)):
            delta = events[i]["date"] - events[i - 1]["date"]
            intervals.append(delta.days)
        return intervals

    def check_47_day_pattern(self, intervals: list[int], tolerance: int = 2) -> dict:
        """Test if crashes cluster around 47-day intervals.

        Uses chi-squared goodness-of-fit test comparing observed frequency
        of 47-day intervals vs expected under uniform distribution.

        Args:
            intervals: List of day-count intervals between crashes
            tolerance: ±days to count as a "match" (default 2)

        Returns:
            Statistical analysis dict
        """
        if not intervals:
            return {
                "total_intervals": 0,
                "matches_47": 0,
                "match_rate": 0.0,
                "expected_random": 0.0,
                "chi_squared": 0.0,
                "p_value": 1.0,
                "is_significant": False,
                "conclusion": "Insufficient data for analysis",
            }

        total = len(intervals)
        target = 47

        # Count matches within tolerance
        matches = sum(
            1 for iv in intervals if abs(iv - target) <= tolerance
        )
        match_rate = matches / total if total > 0 else 0.0

        # Also check multiples of 47 (2x, 3x, etc.)
        multiples = sum(
            1
            for iv in intervals
            if any(abs(iv - target * m) <= tolerance for m in range(1, 6))
        )

        # Expected probability under uniform distribution
        # If intervals range from min to max, probability of hitting
        # 47 ± tolerance is (2*tolerance+1) / (max-min+1)
        if total > 0:
            min_iv = min(intervals)
            max_iv = max(intervals)
            range_size = max_iv - min_iv + 1
            window = 2 * tolerance + 1
            expected_prob = min(window / range_size, 1.0) if range_size > 0 else 0
            expected_count = total * expected_prob
        else:
            expected_prob = 0
            expected_count = 0

        # Chi-squared test
        try:
            from scipy.stats import chi2

            if expected_count > 0:
                chi_sq = ((matches - expected_count) ** 2) / expected_count
                p_value = 1 - chi2.cdf(chi_sq, df=1)
            else:
                chi_sq = 0.0
                p_value = 1.0
        except ImportError:
            logger.warning("scipy not installed — skipping chi-squared test")
            chi_sq = 0.0
            p_value = 1.0

        is_significant = p_value < 0.05

        if is_significant and matches > expected_count:
            conclusion = (
                f"SIGNIFICANT: 47-day crash cycle appears real. "
                f"{matches}/{total} intervals match (expected {expected_count:.1f}). "
                f"p-value: {p_value:.4f}"
            )
        elif matches > expected_count:
            conclusion = (
                f"SUGGESTIVE but not statistically significant. "
                f"{matches}/{total} intervals match (expected {expected_count:.1f}). "
                f"p-value: {p_value:.4f}"
            )
        else:
            conclusion = (
                f"NOT SUPPORTED: 47-day cycle not evident. "
                f"{matches}/{total} intervals match (expected {expected_count:.1f}). "
                f"p-value: {p_value:.4f}"
            )

        return {
            "total_intervals": total,
            "matches_47": matches,
            "multiples_47": multiples,
            "match_rate": round(match_rate, 4),
            "expected_random": round(expected_count, 2),
            "chi_squared": round(chi_sq, 4),
            "p_value": round(p_value, 4),
            "is_significant": is_significant,
            "conclusion": conclusion,
            "interval_distribution": dict(Counter(intervals)),
            "mean_interval": round(sum(intervals) / len(intervals), 1) if intervals else 0,
            "median_interval": sorted(intervals)[len(intervals) // 2] if intervals else 0,
        }

    def cross_reference_celestial(
        self, db: Session, events: list[dict]
    ) -> dict:
        """Analyze celestial state at each crash event.

        Returns:
            Distribution of lunar phases, retrograde status, etc. at crash times.
        """
        lunar_phases = Counter()
        mercury_retro_count = 0
        total_with_data = 0

        for event in events:
            ts = datetime(
                event["date"].year, event["date"].month, event["date"].day,
                tzinfo=timezone.utc,
            )
            state = db.execute(
                select(CelestialState).where(CelestialState.timestamp == ts)
            ).scalar_one_or_none()

            if state:
                total_with_data += 1
                if state.lunar_phase_name:
                    lunar_phases[state.lunar_phase_name] += 1
                if state.mercury_retrograde:
                    mercury_retro_count += 1

        return {
            "total_events": len(events),
            "events_with_celestial_data": total_with_data,
            "lunar_phase_distribution": dict(lunar_phases),
            "mercury_retrograde_count": mercury_retro_count,
            "mercury_retrograde_pct": (
                round(mercury_retro_count / total_with_data * 100, 1)
                if total_with_data > 0
                else 0
            ),
            # Mercury is retrograde ~19% of the time, so >19% is notable
            "mercury_retro_above_baseline": (
                mercury_retro_count / total_with_data > 0.19
                if total_with_data > 0
                else False
            ),
        }

    def cross_reference_numerology(
        self, db: Session, events: list[dict]
    ) -> dict:
        """Analyze numerological state at each crash event.

        Returns:
            Distribution of universal day numbers and master number frequency.
        """
        udn_distribution = Counter()
        master_count = 0
        total_with_data = 0

        for event in events:
            num = db.execute(
                select(NumerologyDaily).where(NumerologyDaily.date == event["date"])
            ).scalar_one_or_none()

            if num:
                total_with_data += 1
                if num.universal_day_number:
                    udn_distribution[num.universal_day_number] += 1
                if num.is_master_number:
                    master_count += 1

        return {
            "total_events": len(events),
            "events_with_numerology_data": total_with_data,
            "universal_day_number_distribution": dict(udn_distribution),
            "master_number_count": master_count,
            "master_number_pct": (
                round(master_count / total_with_data * 100, 1)
                if total_with_data > 0
                else 0
            ),
        }

    def generate_report(
        self,
        db: Session,
        symbol: str = "BTC/USDT",
        min_magnitude: float = -10.0,
    ) -> dict:
        """Generate a comprehensive 47-day cycle backtest report.

        Returns:
            Full report dict with statistical analysis and cross-references.
        """
        logger.info("Generating 47-day cycle report for %s (min: %.1f%%)", symbol, min_magnitude)

        events = self.get_crash_events(db, symbol, min_magnitude)
        intervals = self.compute_intervals(events)

        report = {
            "symbol": symbol,
            "min_magnitude_pct": min_magnitude,
            "total_crash_events": len(events),
            "date_range": {
                "start": events[0]["date"].isoformat() if events else None,
                "end": events[-1]["date"].isoformat() if events else None,
            },
            "cycle_analysis": self.check_47_day_pattern(intervals),
            "celestial_cross_reference": self.cross_reference_celestial(db, events),
            "numerology_cross_reference": self.cross_reference_numerology(db, events),
        }

        logger.info(
            "Report complete: %d crashes, 47-day significant=%s",
            len(events),
            report["cycle_analysis"]["is_significant"],
        )
        return report


class SignalBacktester:
    """Replay historical data to measure signal accuracy."""

    def __init__(self):
        self.engine = ConfluenceEngine()

    def replay_historical(
        self,
        db: Session,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        start: date | None = None,
        end: date | None = None,
    ) -> list[dict]:
        """Replay historical data and compute what confluence scores would have been.

        For each day: gather layer scores, compute composite, compare to actual
        price movement in the following 1d/7d.

        Returns:
            List of {date, composite_score, signal_strength, price_change_1d, price_change_7d}
        """
        start_date = start or date(2020, 6, 1)  # Need enough TA data
        end_date = end or date.today() - timedelta(days=7)  # Need 7d forward data

        # Get all daily close prices
        prices = db.execute(
            select(PriceData)
            .where(
                PriceData.symbol == symbol,
                PriceData.timeframe == timeframe,
                PriceData.timestamp >= datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc),
            )
            .order_by(PriceData.timestamp.asc())
        ).scalars().all()

        price_map = {p.timestamp.date(): float(p.close) for p in prices if p.close}

        # Get all TA scores
        ta_rows = db.execute(
            select(TAIndicators)
            .where(
                TAIndicators.symbol == symbol,
                TAIndicators.timeframe == timeframe,
            )
            .order_by(TAIndicators.timestamp.asc())
        ).scalars().all()
        ta_map = {r.timestamp.date(): float(r.ta_score) for r in ta_rows if r.ta_score}

        # Get all celestial scores
        cel_rows = db.execute(
            select(CelestialState).order_by(CelestialState.timestamp.asc())
        ).scalars().all()
        cel_map = {r.timestamp.date(): float(r.celestial_score) for r in cel_rows if r.celestial_score}

        # Get all numerology scores
        num_rows = db.execute(
            select(NumerologyDaily).order_by(NumerologyDaily.date.asc())
        ).scalars().all()
        num_map = {r.date: float(r.numerology_score) for r in num_rows if r.numerology_score}

        # Get all sentiment scores
        sent_rows = db.execute(
            select(SentimentData)
            .where(SentimentData.symbol == symbol)
            .order_by(SentimentData.timestamp.asc())
        ).scalars().all()
        sent_map = {r.timestamp.date(): float(r.sentiment_score) for r in sent_rows if r.sentiment_score}

        weights = self.engine.get_active_weights(db)
        results = []

        current = start_date
        while current <= end_date:
            scores = {
                "ta_score": ta_map.get(current),
                "celestial_score": cel_map.get(current),
                "numerology_score": num_map.get(current),
                "sentiment_score": sent_map.get(current),
                "onchain_score": None,
                "political_score": None,
            }

            # Need at least TA score
            if scores["ta_score"] is None:
                current += timedelta(days=1)
                continue

            result = self.engine.compute_composite(scores, weights)

            # Forward price changes
            price_today = price_map.get(current)
            price_1d = price_map.get(current + timedelta(days=1))
            price_7d = price_map.get(current + timedelta(days=7))

            change_1d = None
            change_7d = None
            if price_today and price_1d:
                change_1d = round((price_1d - price_today) / price_today * 100, 4)
            if price_today and price_7d:
                change_7d = round((price_7d - price_today) / price_today * 100, 4)

            results.append({
                "date": current.isoformat(),
                "composite_score": result["composite_score"],
                "signal_strength": result["signal_strength"],
                "scores": {k: v for k, v in scores.items() if v is not None},
                "price_change_1d_pct": change_1d,
                "price_change_7d_pct": change_7d,
            })

            current += timedelta(days=1)

        return results

    def compute_accuracy(self, predictions: list[dict]) -> dict:
        """Compute hit rate from replay results.

        A "hit" is when:
        - composite > +0.3 and price went up (1d or 7d)
        - composite < -0.3 and price went down (1d or 7d)

        Returns:
            Accuracy metrics dict
        """
        bullish_signals = []
        bearish_signals = []

        for p in predictions:
            score = p["composite_score"]
            change_1d = p.get("price_change_1d_pct")
            change_7d = p.get("price_change_7d_pct")

            if score > 0.3 and change_1d is not None:
                bullish_signals.append({
                    "date": p["date"],
                    "score": score,
                    "change_1d": change_1d,
                    "change_7d": change_7d,
                    "hit_1d": change_1d > 0,
                    "hit_7d": change_7d > 0 if change_7d is not None else None,
                })
            elif score < -0.3 and change_1d is not None:
                bearish_signals.append({
                    "date": p["date"],
                    "score": score,
                    "change_1d": change_1d,
                    "change_7d": change_7d,
                    "hit_1d": change_1d < 0,
                    "hit_7d": change_7d < 0 if change_7d is not None else None,
                })

        total_signals = len(bullish_signals) + len(bearish_signals)

        bull_hits_1d = sum(1 for s in bullish_signals if s["hit_1d"])
        bear_hits_1d = sum(1 for s in bearish_signals if s["hit_1d"])
        total_hits_1d = bull_hits_1d + bear_hits_1d

        bull_hits_7d = sum(1 for s in bullish_signals if s.get("hit_7d"))
        bear_hits_7d = sum(1 for s in bearish_signals if s.get("hit_7d"))
        total_hits_7d = bull_hits_7d + bear_hits_7d
        total_7d = sum(1 for s in bullish_signals + bearish_signals if s.get("hit_7d") is not None)

        avg_return_1d = 0.0
        if bullish_signals or bearish_signals:
            all_returns = [s["change_1d"] for s in bullish_signals]
            all_returns += [-s["change_1d"] for s in bearish_signals]  # Flip sign for shorts
            avg_return_1d = round(sum(all_returns) / len(all_returns), 4) if all_returns else 0.0

        return {
            "total_signals": total_signals,
            "bullish_signals": len(bullish_signals),
            "bearish_signals": len(bearish_signals),
            "hit_rate_1d": round(total_hits_1d / total_signals, 4) if total_signals > 0 else 0,
            "hit_rate_7d": round(total_hits_7d / total_7d, 4) if total_7d > 0 else 0,
            "avg_return_per_signal_1d_pct": avg_return_1d,
            "bullish_hit_rate_1d": (
                round(bull_hits_1d / len(bullish_signals), 4) if bullish_signals else 0
            ),
            "bearish_hit_rate_1d": (
                round(bear_hits_1d / len(bearish_signals), 4) if bearish_signals else 0
            ),
        }

    def optimize_weights(
        self,
        db: Session,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
    ) -> dict:
        """Grid search for optimal layer weights.

        Tests weight combinations in 0.1 increments for available layers.
        Returns the combination with the highest 7-day hit rate.
        """
        logger.info("Starting weight optimization for %s %s", symbol, timeframe)

        # Get historical data once
        replay_data = self.replay_historical(db, symbol, timeframe)
        if not replay_data:
            return {"error": "No historical data available for replay"}

        # Determine which layers have data
        available_layers = set()
        for r in replay_data:
            for layer, val in r["scores"].items():
                if val is not None:
                    available_layers.add(layer.replace("_score", ""))

        if not available_layers:
            return {"error": "No layer scores available"}

        # Generate weight combinations (0.1 increments, sum to 1.0)
        layer_list = sorted(available_layers)
        n_layers = len(layer_list)
        steps = [round(x * 0.1, 1) for x in range(1, 10)]  # 0.1 to 0.9

        best_hit_rate = -1
        best_weights = {}
        combos_tested = 0

        # For efficiency, only test a subset if too many layers
        if n_layers <= 4:
            weight_options = [s for s in steps]
            for combo in product(weight_options, repeat=n_layers):
                if abs(sum(combo) - 1.0) > 0.01:
                    continue

                weights = {
                    layer: w
                    for layer, w in zip(layer_list, combo)
                }
                # Add zero weight for missing layers
                for key in ["ta", "onchain", "celestial", "numerology", "sentiment", "political"]:
                    weights.setdefault(key, 0.0)

                # Re-compute composite with these weights
                results = []
                for r in replay_data:
                    scores = {}
                    for layer in ["ta", "onchain", "celestial", "numerology", "sentiment", "political"]:
                        scores[f"{layer}_score"] = r["scores"].get(f"{layer}_score")
                    composite = self._quick_composite(scores, weights)
                    results.append({
                        **r,
                        "composite_score": composite,
                    })

                accuracy = self.compute_accuracy(results)
                combos_tested += 1

                if accuracy["hit_rate_7d"] > best_hit_rate and accuracy["total_signals"] >= 5:
                    best_hit_rate = accuracy["hit_rate_7d"]
                    best_weights = {k: v for k, v in weights.items() if v > 0}
        else:
            # With many layers, just test a few reasonable combos
            best_weights = {l: round(1.0 / n_layers, 2) for l in layer_list}
            best_hit_rate = 0

        logger.info(
            "Weight optimization complete: tested %d combos, best 7d hit rate: %.4f",
            combos_tested,
            best_hit_rate,
        )

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "combos_tested": combos_tested,
            "available_layers": list(available_layers),
            "best_weights": best_weights,
            "best_hit_rate_7d": round(best_hit_rate, 4),
        }

    def _quick_composite(self, scores: dict, weights: dict) -> float:
        """Quick composite computation without DB access."""
        score_to_weight = {
            "ta_score": "ta",
            "onchain_score": "onchain",
            "celestial_score": "celestial",
            "numerology_score": "numerology",
            "sentiment_score": "sentiment",
            "political_score": "political",
        }

        available = {}
        for score_key, weight_key in score_to_weight.items():
            val = scores.get(score_key)
            if val is not None:
                w = weights.get(weight_key, 0)
                if w > 0:
                    available[score_key] = (val, w)

        if not available:
            return 0.0

        total_weight = sum(w for _, w in available.values())
        if total_weight == 0:
            return 0.0

        composite = sum(val * (w / total_weight) for val, w in available.values())
        return round(max(-1.0, min(1.0, composite)), 4)
