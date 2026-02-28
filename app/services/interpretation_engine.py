"""Claude-powered signal interpretation engine.

Gathers live data from all 7 signal layers, sends structured context to
Claude Haiku, and returns a plain-English market analysis. Results are
cached in-memory for 30 minutes to manage API costs.
"""

import json
import logging
import time
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.celestial_state import CelestialState
from app.models.numerology_daily import NumerologyDaily
from app.models.political_signal import PoliticalSignal
from app.models.sentiment_data import SentimentData
from app.models.ta_indicators import TAIndicators
from app.services.confluence_engine import ConfluenceEngine

logger = logging.getLogger(__name__)

# In-memory cache: {cache_key: (timestamp_seconds, result_dict)}
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 30 * 60  # 30 minutes

SYSTEM_PROMPT = """\
You are CryptoOracle's AI analyst. Given the signal layer data below, \
produce a concise market interpretation. Be specific to the numbers shown — \
don't give generic advice.

Respond in this exact JSON format (no markdown fences):
{
  "summary": "2-3 sentence overview of the combined signal picture",
  "layers": {
    "ta": "one sentence on TA (only if data present)",
    "sentiment": "one sentence on sentiment (only if data present)",
    "political": "one sentence on political (only if data present)",
    "macro": "one sentence on macro (only if data present)",
    "celestial": "one sentence on celestial (only if data present)",
    "numerology": "one sentence on numerology (only if data present)"
  },
  "watch": "one key thing to watch for next",
  "bias": "one of: strongly_bullish, bullish, cautiously_bullish, neutral, cautiously_bearish, bearish, strongly_bearish"
}

Only include layers in the "layers" object that have actual data (non-null scores). \
Keep each layer insight to one sentence. Be direct and actionable.\
"""


class InterpretationEngine:
    """Generates AI-powered interpretations of confluence signals."""

    def interpret(
        self, db: Session, symbol: str, timeframe: str = "1h",
        force: bool = False,
    ) -> dict:
        """Generate or return cached interpretation for a symbol.

        Returns dict with: summary, layers, watch, bias, generated_at, cached.
        When *force* is True the cache is bypassed (but the new result is still cached).
        """
        if not settings.anthropic_api_key:
            return {
                "summary": "Configure ANTHROPIC_API_KEY to enable AI interpretation.",
                "layers": {},
                "watch": "",
                "bias": "neutral",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

        cache_key = f"{symbol}:{timeframe}"
        now = time.time()

        # Check cache (skip when force-refreshing)
        if not force and cache_key in _cache:
            cached_at, cached_result = _cache[cache_key]
            if now - cached_at < CACHE_TTL_SECONDS:
                return {**cached_result, "cached": True}

        # Gather all layer data
        context = self._gather_context(db, symbol, timeframe)

        # Call Claude
        result = self._call_claude(symbol, timeframe, context)
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["cached"] = False

        # Cache result
        _cache[cache_key] = (now, result)

        return result

    def _gather_context(
        self, db: Session, symbol: str, timeframe: str
    ) -> dict:
        """Gather data from all layers into a single context dict."""
        engine = ConfluenceEngine()
        scores = engine.gather_latest_scores(db, symbol, timeframe)
        weights = engine.get_active_weights(db)
        composite = engine.compute_composite(scores, weights)

        context: dict = {
            "symbol": symbol,
            "timeframe": timeframe,
            "composite_score": composite["composite_score"],
            "signal_strength": composite["signal_strength"],
            "alignment_count": composite["alignment_count"],
            "aligned_layers": composite["aligned_layers"],
            "layer_scores": scores,
        }

        # TA indicators
        ta_row = db.execute(
            select(TAIndicators)
            .where(
                TAIndicators.symbol == symbol,
                TAIndicators.timeframe == timeframe,
            )
            .order_by(TAIndicators.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        if ta_row:
            context["ta"] = {
                "rsi_14": _f(ta_row.rsi_14),
                "macd_line": _f(ta_row.macd_line),
                "macd_signal": _f(ta_row.macd_signal),
                "macd_histogram": _f(ta_row.macd_histogram),
                "stoch_k": _f(ta_row.stoch_k),
                "stoch_d": _f(ta_row.stoch_d),
                "sma_20": _f(ta_row.sma_20),
                "sma_50": _f(ta_row.sma_50),
                "sma_200": _f(ta_row.sma_200),
                "bb_upper": _f(ta_row.bb_upper),
                "bb_lower": _f(ta_row.bb_lower),
                "atr_14": _f(ta_row.atr_14),
            }

        # Sentiment
        sent_row = db.execute(
            select(SentimentData)
            .where(SentimentData.symbol == symbol)
            .order_by(SentimentData.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        if sent_row:
            context["sentiment"] = {
                "fear_greed_index": sent_row.fear_greed_index,
                "fear_greed_label": sent_row.fear_greed_label,
            }

        # Political
        pol_row = db.execute(
            select(PoliticalSignal)
            .order_by(PoliticalSignal.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()
        if pol_row:
            context["political"] = {
                "news_volume_24h": pol_row.news_volume_24h,
                "dominant_narrative": pol_row.dominant_narrative,
                "narrative_direction": pol_row.narrative_direction,
                "next_event_type": pol_row.next_event_type,
                "hours_to_next_major_event": pol_row.hours_to_next_major_event,
            }

        # Macro — import here to avoid circular
        try:
            from app.models.macro_liquidity import MacroLiquiditySignal

            macro_row = db.execute(
                select(MacroLiquiditySignal)
                .order_by(MacroLiquiditySignal.timestamp.desc())
                .limit(1)
            ).scalar_one_or_none()
            if macro_row:
                context["macro"] = {
                    "regime": macro_row.regime,
                    "sub_signals": macro_row.sub_signals,
                    "data_points": macro_row.data_points,
                }
        except Exception:
            pass

        # Celestial
        today = date.today()
        today_start = datetime(
            today.year, today.month, today.day, tzinfo=timezone.utc
        )
        cel_row = db.execute(
            select(CelestialState)
            .where(CelestialState.timestamp == today_start)
        ).scalar_one_or_none()
        if cel_row:
            context["celestial"] = {
                "lunar_phase_name": cel_row.lunar_phase_name,
                "lunar_illumination": _f(cel_row.lunar_illumination),
                "retrograde_count": cel_row.retrograde_count,
                "mercury_retrograde": cel_row.mercury_retrograde,
                "jupiter_retrograde": cel_row.jupiter_retrograde,
                "days_to_next_full_moon": _f(cel_row.days_to_next_full_moon),
                "is_lunar_eclipse": cel_row.is_lunar_eclipse,
                "is_solar_eclipse": cel_row.is_solar_eclipse,
            }

        # Numerology
        num_row = db.execute(
            select(NumerologyDaily).where(NumerologyDaily.date == today)
        ).scalar_one_or_none()
        if num_row:
            context["numerology"] = {
                "universal_day_number": num_row.universal_day_number,
                "is_master_number": num_row.is_master_number,
                "cycle_confluence_count": num_row.cycle_confluence_count,
                "numerology_score": _f(num_row.numerology_score),
            }

        return context

    def _call_claude(
        self, symbol: str, timeframe: str, context: dict
    ) -> dict:
        """Call Claude Haiku and parse the JSON response."""
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        user_message = (
            f"Signal data for {symbol} ({timeframe}):\n\n"
            f"{json.dumps(context, indent=2, default=str)}"
        )

        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            raw = message.content[0].text.strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            parsed = json.loads(raw)
            return {
                "summary": parsed.get("summary", ""),
                "layers": parsed.get("layers", {}),
                "watch": parsed.get("watch", ""),
                "bias": parsed.get("bias", "neutral"),
            }

        except json.JSONDecodeError:
            logger.warning("Failed to parse Claude response as JSON: %s", raw[:200])
            return {
                "summary": raw[:500] if raw else "Interpretation unavailable.",
                "layers": {},
                "watch": "",
                "bias": "neutral",
            }
        except Exception:
            logger.exception("Claude API call failed")
            return {
                "summary": "AI interpretation temporarily unavailable.",
                "layers": {},
                "watch": "",
                "bias": "neutral",
            }


    def chat(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        messages: list[dict],
    ) -> str:
        """Answer a follow-up question using live signal context.

        *messages* is the full conversation history
        ``[{"role": "user", "content": "..."}, ...]``.

        Returns the assistant's plain-text reply.
        """
        import anthropic

        if not settings.anthropic_api_key:
            return "Configure ANTHROPIC_API_KEY to enable chat."

        context = self._gather_context(db, symbol, timeframe)

        # Grab latest cached interpretation summary if available
        cache_key = f"{symbol}:{timeframe}"
        cached_summary = ""
        if cache_key in _cache:
            _, cached_result = _cache[cache_key]
            cached_summary = cached_result.get("summary", "")

        system = (
            "You are CryptoOracle's AI market analyst. You have access to real-time "
            f"signal data for {symbol}. Answer questions about these signals directly "
            "and specifically, referencing the actual numbers shown below.\n\n"
            f"Current signal data:\n{json.dumps(context, indent=2, default=str)}"
        )
        if cached_summary:
            system += f"\n\nCurrent AI interpretation:\n{cached_summary}"

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except Exception:
            logger.exception("Chat API call failed for %s", symbol)
            return "Sorry, I couldn't process that request. Please try again."


def _f(val) -> float | None:
    """Safely convert a Decimal/string to float."""
    if val is None:
        return None
    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None
