"""Alert engine — generates alerts from confluence scores and special conditions.

Checks for confluence threshold crossings, layer alignment, cycle proximity,
celestial events, and extreme sentiment. Deduplicates alerts to prevent spam.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alerts import Alerts
from app.models.celestial_state import CelestialState
from app.models.sentiment_data import SentimentData
from app.services import cycle_tracker

logger = logging.getLogger(__name__)


class AlertEngine:
    """Generate alerts based on signal conditions."""

    def check_confluence_alerts(
        self, db: Session, symbol: str, confluence_result: dict
    ) -> list[dict]:
        """Check if confluence score triggers an alert.

        Triggers:
        - composite_score crosses ±0.5 → "confluence" alert
        - alignment_count >= 4 → "alignment" alert
        - signal_strength is strong_buy/strong_sell → "extreme_signal" alert
        """
        alerts = []
        score = confluence_result.get("composite_score", 0)
        strength = confluence_result.get("signal_strength", "neutral")
        alignment = confluence_result.get("alignment_count", 0)

        if score >= 0.5:
            alerts.append({
                "symbol": symbol,
                "alert_type": "confluence",
                "severity": "warning",
                "title": f"High confluence bullish: {symbol} ({score:+.4f})",
                "description": f"Composite score {score:+.4f} crossed +0.5 threshold. "
                               f"Signal: {strength}. Aligned layers: {alignment}.",
                "composite_score": score,
                "aligned_layers": confluence_result.get("aligned_layers"),
                "trigger_data": confluence_result,
            })
        elif score <= -0.5:
            alerts.append({
                "symbol": symbol,
                "alert_type": "confluence",
                "severity": "warning",
                "title": f"High confluence bearish: {symbol} ({score:+.4f})",
                "description": f"Composite score {score:+.4f} crossed -0.5 threshold. "
                               f"Signal: {strength}. Aligned layers: {alignment}.",
                "composite_score": score,
                "aligned_layers": confluence_result.get("aligned_layers"),
                "trigger_data": confluence_result,
            })

        if alignment >= 4:
            direction = confluence_result.get("aligned_layers", {}).get("direction", "unknown")
            alerts.append({
                "symbol": symbol,
                "alert_type": "alignment",
                "severity": "info",
                "title": f"Layer alignment: {alignment} layers {direction} on {symbol}",
                "description": f"{alignment} signal layers agree on {direction} direction.",
                "composite_score": score,
                "aligned_layers": confluence_result.get("aligned_layers"),
                "trigger_data": confluence_result,
            })

        if strength in ("strong_buy", "strong_sell"):
            alerts.append({
                "symbol": symbol,
                "alert_type": "extreme_signal",
                "severity": "critical",
                "title": f"Extreme signal: {strength.upper()} on {symbol}",
                "description": f"Composite score {score:+.4f} indicates {strength}.",
                "composite_score": score,
                "aligned_layers": confluence_result.get("aligned_layers"),
                "trigger_data": confluence_result,
            })

        return alerts

    def check_cycle_alerts(self, db: Session, d: date) -> list[dict]:
        """Check if any custom cycles are near alignment.

        Triggers when a cycle is within 3 days of its target date.
        """
        alerts = []
        try:
            alignments = cycle_tracker.check_date(db, d)
        except Exception:
            logger.exception("Error checking cycle alignments")
            return []

        for a in alignments:
            if a.get("is_aligned"):
                days_off = a.get("days_offset", 0)
                severity = "critical" if abs(days_off) <= 1 else "warning"
                alerts.append({
                    "symbol": "BTC/USDT",  # Cycles are market-wide
                    "alert_type": "cycle_alignment",
                    "severity": severity,
                    "title": f"Cycle alignment: {a['cycle_name']} (day offset: {days_off:+d})",
                    "description": (
                        f"{a['cycle_name']} ({a['cycle_days']}-day cycle) aligns "
                        f"with {d.isoformat()}. Days from exact: {days_off:+d}."
                    ),
                    "trigger_data": a,
                })

        return alerts

    def check_celestial_alerts(self, db: Session, d: date) -> list[dict]:
        """Check for noteworthy celestial events.

        Triggers:
        - Mercury retrograde starts/ends (compare today vs yesterday)
        - Eclipse within 48 hours
        """
        alerts = []

        today_ts = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        yesterday_ts = today_ts - timedelta(days=1)

        today_state = db.execute(
            select(CelestialState).where(CelestialState.timestamp == today_ts)
        ).scalar_one_or_none()

        if not today_state:
            return []

        yesterday_state = db.execute(
            select(CelestialState).where(CelestialState.timestamp == yesterday_ts)
        ).scalar_one_or_none()

        # Mercury retrograde transition
        if yesterday_state:
            if today_state.mercury_retrograde and not yesterday_state.mercury_retrograde:
                alerts.append({
                    "symbol": "BTC/USDT",
                    "alert_type": "celestial_event",
                    "severity": "warning",
                    "title": "Mercury retrograde begins",
                    "description": "Mercury retrograde started today. Historically correlates with increased volatility and reversals.",
                    "trigger_data": {"event": "mercury_retrograde_start", "date": d.isoformat()},
                })
            elif not today_state.mercury_retrograde and yesterday_state.mercury_retrograde:
                alerts.append({
                    "symbol": "BTC/USDT",
                    "alert_type": "celestial_event",
                    "severity": "info",
                    "title": "Mercury retrograde ends",
                    "description": "Mercury retrograde ended today.",
                    "trigger_data": {"event": "mercury_retrograde_end", "date": d.isoformat()},
                })

        # Eclipse within 48 hours
        if today_state.is_lunar_eclipse:
            alerts.append({
                "symbol": "BTC/USDT",
                "alert_type": "celestial_event",
                "severity": "warning",
                "title": "Lunar eclipse today",
                "description": "Lunar eclipse occurring today. High volatility expected.",
                "trigger_data": {"event": "lunar_eclipse", "date": d.isoformat()},
            })
        if today_state.is_solar_eclipse:
            alerts.append({
                "symbol": "BTC/USDT",
                "alert_type": "celestial_event",
                "severity": "warning",
                "title": "Solar eclipse today",
                "description": "Solar eclipse occurring today. High volatility expected.",
                "trigger_data": {"event": "solar_eclipse", "date": d.isoformat()},
            })

        return alerts

    def check_sentiment_alerts(self, db: Session, symbol: str) -> list[dict]:
        """Check for extreme sentiment conditions.

        Triggers when Fear & Greed < 10 or > 90.
        """
        alerts = []

        row = db.execute(
            select(SentimentData)
            .where(SentimentData.symbol == symbol)
            .order_by(SentimentData.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if not row or row.fear_greed_index is None:
            return []

        fg = row.fear_greed_index
        if fg <= 10:
            alerts.append({
                "symbol": symbol,
                "alert_type": "extreme_sentiment",
                "severity": "critical",
                "title": f"Extreme Fear: F&G Index at {fg}",
                "description": f"Fear & Greed Index is {fg} (Extreme Fear). "
                               "Historically a contrarian buy signal.",
                "trigger_data": {"fear_greed_index": fg, "label": row.fear_greed_label},
            })
        elif fg >= 90:
            alerts.append({
                "symbol": symbol,
                "alert_type": "extreme_sentiment",
                "severity": "critical",
                "title": f"Extreme Greed: F&G Index at {fg}",
                "description": f"Fear & Greed Index is {fg} (Extreme Greed). "
                               "Historically a contrarian sell signal.",
                "trigger_data": {"fear_greed_index": fg, "label": row.fear_greed_label},
            })

        return alerts

    def create_alert(self, db: Session, alert_data: dict) -> bool:
        """Insert an alert into the alerts table.

        Deduplicates: skips if an active alert with the same type + symbol
        already exists within the last 24 hours.

        Returns:
            True if alert was created, False if deduplicated.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        existing = db.execute(
            select(Alerts).where(
                Alerts.alert_type == alert_data["alert_type"],
                Alerts.symbol == alert_data["symbol"],
                Alerts.status == "active",
                Alerts.created_at >= cutoff,
            )
        ).scalar_one_or_none()

        if existing:
            return False

        alert = Alerts(
            triggered_at=datetime.now(timezone.utc),
            symbol=alert_data["symbol"],
            alert_type=alert_data["alert_type"],
            severity=alert_data["severity"],
            title=alert_data["title"],
            description=alert_data.get("description"),
            trigger_data=alert_data.get("trigger_data"),
            composite_score=alert_data.get("composite_score"),
            aligned_layers=alert_data.get("aligned_layers"),
            status="active",
        )
        db.add(alert)
        db.commit()
        logger.info("Alert created: [%s] %s", alert_data["severity"], alert_data["title"])
        return True

    def run_all_checks(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        confluence_result: dict,
    ) -> int:
        """Run all alert checks and create any triggered alerts.

        Returns:
            Number of new alerts created.
        """
        today = date.today()
        created = 0

        all_alerts = []
        all_alerts.extend(self.check_confluence_alerts(db, symbol, confluence_result))
        all_alerts.extend(self.check_cycle_alerts(db, today))
        all_alerts.extend(self.check_celestial_alerts(db, today))
        all_alerts.extend(self.check_sentiment_alerts(db, symbol))

        for alert_data in all_alerts:
            if self.create_alert(db, alert_data):
                created += 1

        if created:
            logger.info("Alert check for %s: %d new alerts created", symbol, created)
        return created
