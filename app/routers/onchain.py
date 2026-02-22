"""On-chain metrics API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.onchain_metrics import OnchainMetrics

router = APIRouter(tags=["onchain"])


@router.get("/api/onchain/status")
def get_onchain_status():
    """Check which on-chain data providers are configured."""
    return {
        "cryptoquant": {
            "configured": bool(settings.cryptoquant_api_key),
            "provides": ["exchange_flows", "whale_activity"],
        },
        "glassnode": {
            "configured": bool(settings.glassnode_api_key),
            "provides": ["nupl", "mvrv_zscore", "sopr", "active_addresses"],
        },
        "any_available": bool(settings.cryptoquant_api_key or settings.glassnode_api_key),
    }


@router.get("/api/onchain/{symbol}")
def get_latest_onchain(symbol: str, db: Session = Depends(get_db)):
    """Get the latest on-chain metrics for a symbol."""
    row = db.execute(
        select(OnchainMetrics)
        .where(OnchainMetrics.symbol == symbol)
        .order_by(OnchainMetrics.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if row is None:
        has_keys = bool(settings.cryptoquant_api_key or settings.glassnode_api_key)
        msg = (
            "No on-chain data available yet"
            if has_keys
            else "No on-chain API keys configured. Set CRYPTOQUANT_API_KEY and/or GLASSNODE_API_KEY."
        )
        return {"symbol": symbol, "metrics": None, "message": msg}

    return {
        "symbol": symbol,
        "metrics": {
            "timestamp": row.timestamp.isoformat(),
            "exchange_inflow": str(row.exchange_inflow) if row.exchange_inflow else None,
            "exchange_outflow": str(row.exchange_outflow) if row.exchange_outflow else None,
            "exchange_netflow": str(row.exchange_netflow) if row.exchange_netflow else None,
            "whale_transactions_count": row.whale_transactions_count,
            "whale_volume_usd": str(row.whale_volume_usd) if row.whale_volume_usd else None,
            "active_addresses": row.active_addresses,
            "nupl": str(row.nupl) if row.nupl else None,
            "mvrv_zscore": str(row.mvrv_zscore) if row.mvrv_zscore else None,
            "sopr": str(row.sopr) if row.sopr else None,
            "onchain_score": str(row.onchain_score) if row.onchain_score else None,
        },
    }


@router.get("/api/onchain/{symbol}/history")
def get_onchain_history(
    symbol: str,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get historical on-chain metrics for a symbol."""
    query = select(OnchainMetrics).where(OnchainMetrics.symbol == symbol)

    if start:
        query = query.where(OnchainMetrics.timestamp >= start)
    if end:
        query = query.where(OnchainMetrics.timestamp <= end)

    query = query.order_by(OnchainMetrics.timestamp.desc()).limit(limit)
    rows = db.execute(query).scalars().all()

    return {
        "symbol": symbol,
        "count": len(rows),
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "exchange_netflow": str(r.exchange_netflow) if r.exchange_netflow else None,
                "whale_transactions_count": r.whale_transactions_count,
                "nupl": str(r.nupl) if r.nupl else None,
                "mvrv_zscore": str(r.mvrv_zscore) if r.mvrv_zscore else None,
                "sopr": str(r.sopr) if r.sopr else None,
                "onchain_score": str(r.onchain_score) if r.onchain_score else None,
            }
            for r in rows
        ],
    }
