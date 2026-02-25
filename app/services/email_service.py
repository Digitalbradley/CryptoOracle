"""Email notification service for alert delivery via SMTP."""

import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)

DASHBOARD_URL = "https://web-production-8304e.up.railway.app"

# ---------------------------------------------------------------------------
# Rate limiting: max 10 emails per hour
# ---------------------------------------------------------------------------
_send_times: list[float] = []
MAX_PER_HOUR = 10


def _rate_limited() -> bool:
    """Return True if we've exceeded the hourly email limit."""
    now = time.time()
    cutoff = now - 3600
    _send_times[:] = [t for t in _send_times if t > cutoff]
    return len(_send_times) >= MAX_PER_HOUR


def _is_configured() -> bool:
    return bool(settings.alert_email and settings.smtp_user and settings.smtp_password)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_alert_email(alert) -> bool:
    """Send an email notification for a triggered alert.

    Returns True if sent, False if skipped or failed.
    Never raises — errors are logged and swallowed.
    """
    if not _is_configured():
        return False

    if _rate_limited():
        logger.warning("Email rate limit reached (%d/hr), skipping: %s", MAX_PER_HOUR, alert.title)
        return False

    try:
        subject = f"[CryptoOracle] {alert.severity.upper()}: {alert.symbol} — {alert.title}"

        body_plain = _build_plain_body(alert)
        body_html = _build_html_body(alert)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_user
        msg["To"] = settings.alert_email
        msg.attach(MIMEText(body_plain, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, settings.alert_email, msg.as_string())

        _send_times.append(time.time())
        logger.info("Alert email sent: %s — %s", alert.symbol, alert.title)
        return True

    except Exception:
        logger.exception("Failed to send alert email: %s", alert.title)
        return False


# ---------------------------------------------------------------------------
# Email body builders
# ---------------------------------------------------------------------------

def _format_trigger_data(trigger_data: dict | None) -> str:
    """Format trigger_data dict into readable lines."""
    if not trigger_data:
        return ""
    lines = []
    for key, value in trigger_data.items():
        label = key.replace("_", " ").title()
        if isinstance(value, float):
            lines.append(f"  {label}: {value:.4f}")
        else:
            lines.append(f"  {label}: {value}")
    return "\n".join(lines)


def _build_plain_body(alert) -> str:
    ts = alert.triggered_at or alert.created_at
    time_str = ts.strftime("%Y-%m-%d %H:%M UTC") if ts else "Unknown"

    parts = [
        f"Severity: {alert.severity.upper()}",
        f"Symbol: {alert.symbol}",
        f"Alert: {alert.title}",
        f"Time: {time_str}",
        "",
    ]

    if alert.description:
        parts.append(alert.description)
        parts.append("")

    trigger_str = _format_trigger_data(alert.trigger_data)
    if trigger_str:
        parts.append("Signal Data:")
        parts.append(trigger_str)
        parts.append("")

    parts.append(f"View dashboard: {DASHBOARD_URL}")

    return "\n".join(parts)


def _build_html_body(alert) -> str:
    ts = alert.triggered_at or alert.created_at
    time_str = ts.strftime("%Y-%m-%d %H:%M UTC") if ts else "Unknown"

    severity_colors = {
        "critical": "#ef4444",
        "warning": "#f59e0b",
        "info": "#6b7280",
    }
    color = severity_colors.get(alert.severity, "#6b7280")

    trigger_rows = ""
    if alert.trigger_data:
        for key, value in alert.trigger_data.items():
            label = key.replace("_", " ").title()
            val = f"{value:.4f}" if isinstance(value, float) else str(value)
            trigger_rows += f"<tr><td style='padding:2px 8px;color:#9ca3af;'>{label}</td><td style='padding:2px 8px;color:#e5e7eb;'>{val}</td></tr>"

    return f"""
    <div style="background:#0a0b0f;color:#e5e7eb;padding:24px;font-family:'Inter',sans-serif;max-width:600px;">
        <div style="border-left:4px solid {color};padding-left:16px;margin-bottom:16px;">
            <span style="color:{color};font-weight:700;font-size:12px;text-transform:uppercase;">{alert.severity}</span>
            <h2 style="color:#ffffff;margin:4px 0 0 0;font-size:18px;">{alert.symbol} — {alert.title}</h2>
            <p style="color:#9ca3af;margin:4px 0 0 0;font-size:13px;">{time_str}</p>
        </div>

        {"<p style='color:#d1d5db;font-size:14px;line-height:1.6;'>" + alert.description + "</p>" if alert.description else ""}

        {"<table style='font-size:13px;margin:12px 0;'>" + trigger_rows + "</table>" if trigger_rows else ""}

        <a href="{DASHBOARD_URL}" style="display:inline-block;margin-top:16px;padding:8px 20px;background:#d4a846;color:#0a0b0f;text-decoration:none;border-radius:4px;font-weight:600;font-size:13px;">
            View Dashboard
        </a>

        <p style="color:#4b5563;font-size:11px;margin-top:24px;">CryptoOracle Alert System</p>
    </div>
    """
