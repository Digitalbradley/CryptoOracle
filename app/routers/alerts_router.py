"""Alert management API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alerts import Alerts

router = APIRouter(tags=["alerts"])


@router.get("/api/alerts")
def list_alerts(
    status: str = Query("active"),
    symbol: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List alerts filtered by status and optional symbol."""
    query = select(Alerts)

    if status != "all":
        query = query.where(Alerts.status == status)
    if symbol:
        query = query.where(Alerts.symbol == symbol)

    query = query.order_by(Alerts.created_at.desc()).limit(limit)
    rows = db.execute(query).scalars().all()

    return {
        "count": len(rows),
        "alerts": [_alert_to_dict(r) for r in rows],
    }


@router.get("/api/alerts/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a single alert by ID."""
    row = db.execute(
        select(Alerts).where(Alerts.id == alert_id)
    ).scalar_one_or_none()

    if row is None:
        return {"error": "Alert not found"}

    return _alert_to_dict(row)


@router.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an active alert."""
    row = db.execute(
        select(Alerts).where(Alerts.id == alert_id)
    ).scalar_one_or_none()

    if row is None:
        return {"error": "Alert not found"}

    row.status = "acknowledged"
    row.acknowledged_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "acknowledged", "alert_id": alert_id}


@router.post("/api/alerts/{alert_id}/dismiss")
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    """Dismiss an alert."""
    row = db.execute(
        select(Alerts).where(Alerts.id == alert_id)
    ).scalar_one_or_none()

    if row is None:
        return {"error": "Alert not found"}

    row.status = "dismissed"
    db.commit()

    return {"status": "dismissed", "alert_id": alert_id}


def _alert_to_dict(row: Alerts) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "triggered_at": row.triggered_at.isoformat() if row.triggered_at else None,
        "symbol": row.symbol,
        "alert_type": row.alert_type,
        "severity": row.severity,
        "title": row.title,
        "description": row.description,
        "composite_score": str(row.composite_score) if row.composite_score else None,
        "aligned_layers": row.aligned_layers,
        "trigger_data": row.trigger_data,
        "status": row.status,
        "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None,
    }
