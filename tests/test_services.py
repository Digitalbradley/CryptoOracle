"""Tests for core service logic (no DB or HTTP calls)."""

from app.services.sentiment_fetch import compute_sentiment_score
from app.services.confluence_engine import ConfluenceEngine


class TestSentimentScoring:
    """Test the contrarian Fear & Greed → score mapping."""

    def test_extreme_fear_max_bullish(self):
        # fg < 10 → 1.0
        assert compute_sentiment_score(5) == 1.0

    def test_fear_below_20(self):
        # 10 <= fg < 20 → 0.8
        assert compute_sentiment_score(15) == 0.8

    def test_fear_below_30(self):
        # 20 <= fg < 30 → 0.5
        assert compute_sentiment_score(25) == 0.5

    def test_fear_below_40(self):
        # 30 <= fg < 40 → 0.3
        assert compute_sentiment_score(35) == 0.3

    def test_slight_fear(self):
        # 40 <= fg < 50 → 0.1
        assert compute_sentiment_score(45) == 0.1

    def test_neutral(self):
        # 50 <= fg < 60 → 0.0
        assert compute_sentiment_score(55) == 0.0

    def test_slight_greed(self):
        # 60 <= fg < 70 → -0.1
        assert compute_sentiment_score(65) == -0.1

    def test_greed_below_80(self):
        # 70 <= fg < 80 → -0.3
        assert compute_sentiment_score(75) == -0.3

    def test_greed_below_90(self):
        # 80 <= fg < 90 → -0.5
        assert compute_sentiment_score(85) == -0.5

    def test_extreme_greed_max_bearish(self):
        # fg >= 90 → -0.8
        assert compute_sentiment_score(95) == -0.8


class TestConfluenceComposite:
    """Test the composite score computation logic."""

    def setup_method(self):
        self.engine = ConfluenceEngine()

    def test_all_layers_present(self):
        scores = {
            "ta_score": 0.5,
            "onchain_score": 0.3,
            "celestial_score": 0.2,
            "numerology_score": 0.1,
            "sentiment_score": -0.1,
            "political_score": 0.0,
        }
        weights = {
            "ta": 0.25, "onchain": 0.20, "celestial": 0.15,
            "numerology": 0.10, "sentiment": 0.15, "political": 0.15,
        }
        result = self.engine.compute_composite(scores, weights)
        assert "composite_score" in result
        assert "signal_strength" in result
        assert "alignment_count" in result
        assert -1.0 <= result["composite_score"] <= 1.0

    def test_missing_layers_redistributed(self):
        scores = {
            "ta_score": 0.8,
            "onchain_score": None,
            "celestial_score": 0.6,
            "numerology_score": None,
            "sentiment_score": None,
            "political_score": None,
        }
        weights = {
            "ta": 0.25, "onchain": 0.20, "celestial": 0.15,
            "numerology": 0.10, "sentiment": 0.15, "political": 0.15,
        }
        result = self.engine.compute_composite(scores, weights)
        assert result["composite_score"] is not None
        # Only ta and celestial are available, so composite should be their weighted avg
        assert result["composite_score"] > 0

    def test_all_none_layers(self):
        scores = {
            "ta_score": None, "onchain_score": None, "celestial_score": None,
            "numerology_score": None, "sentiment_score": None, "political_score": None,
        }
        weights = {
            "ta": 0.25, "onchain": 0.20, "celestial": 0.15,
            "numerology": 0.10, "sentiment": 0.15, "political": 0.15,
        }
        result = self.engine.compute_composite(scores, weights)
        assert result["composite_score"] == 0.0
        assert result["signal_strength"] == "neutral"

    def test_signal_strength_strong_buy(self):
        scores = {"ta_score": 0.9, "onchain_score": None, "celestial_score": None,
                  "numerology_score": None, "sentiment_score": None, "political_score": None}
        weights = {"ta": 0.25, "onchain": 0.20, "celestial": 0.15,
                   "numerology": 0.10, "sentiment": 0.15, "political": 0.15}
        result = self.engine.compute_composite(scores, weights)
        assert result["signal_strength"] in ("strong_buy", "buy")

    def test_signal_strength_strong_sell(self):
        scores = {"ta_score": -0.9, "onchain_score": None, "celestial_score": None,
                  "numerology_score": None, "sentiment_score": None, "political_score": None}
        weights = {"ta": 0.25, "onchain": 0.20, "celestial": 0.15,
                   "numerology": 0.10, "sentiment": 0.15, "political": 0.15}
        result = self.engine.compute_composite(scores, weights)
        assert result["signal_strength"] in ("strong_sell", "sell")

    def test_alignment_detection(self):
        scores = {
            "ta_score": 0.5,
            "onchain_score": 0.4,
            "celestial_score": 0.3,
            "numerology_score": 0.3,
            "sentiment_score": -0.5,
            "political_score": None,
        }
        weights = {"ta": 0.25, "onchain": 0.20, "celestial": 0.15,
                   "numerology": 0.10, "sentiment": 0.15, "political": 0.15}
        result = self.engine.compute_composite(scores, weights)
        # ta, onchain, celestial, numerology are all > 0.2 (bullish)
        assert result["alignment_count"] >= 3
