"""Macro Liquidity (Layer 7) API endpoints.

Per brief Section 10:
- GET /api/macro/signal — latest composite + sub-signals + regime
- GET /api/macro/status — which data sources are configured
- GET /api/macro/oil — raw oil data
- GET /api/macro/dollar — raw DXY/VIX data
- GET /api/macro/rates — raw rate/yield data
- GET /api/macro/liquidity — raw M2/Fed data
- GET /api/macro/carry — raw carry trade data
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.macro_liquidity import (
    CarryTradeData,
    LiquidityData,
    MacroLiquiditySignal,
    MacroPrices,
    OilData,
    RateData,
)

router = APIRouter(tags=["macro"])


@router.get("/api/macro/signal")
def get_macro_signal(db: Session = Depends(get_db)):
    """Get latest macro liquidity composite signal."""
    row = db.execute(
        select(MacroLiquiditySignal)
        .order_by(MacroLiquiditySignal.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not row:
        return {"status": "no_data", "message": "No macro signal computed yet."}

    return {
        "timestamp": row.timestamp.isoformat(),
        "macro_score": str(row.macro_score) if row.macro_score else None,
        "regime": row.regime,
        "regime_confidence": str(row.regime_confidence) if row.regime_confidence else None,
        "sub_signals": {
            "liquidity_score": str(row.liquidity_score) if row.liquidity_score else None,
            "treasury_score": str(row.treasury_score) if row.treasury_score else None,
            "dollar_score": str(row.dollar_score) if row.dollar_score else None,
            "oil_score": str(row.oil_score) if row.oil_score else None,
            "carry_trade_score": str(row.carry_trade_score) if row.carry_trade_score else None,
        },
        "data_points": {
            "net_liquidity": str(row.net_liquidity) if row.net_liquidity else None,
            "m2_yoy_pct": str(row.m2_yoy_pct) if row.m2_yoy_pct else None,
            "yield_curve_2s10s": str(row.yield_curve_2s10s) if row.yield_curve_2s10s else None,
            "dxy_value": str(row.dxy_value) if row.dxy_value else None,
            "vix_value": str(row.vix_value) if row.vix_value else None,
            "wti_price": str(row.wti_price) if row.wti_price else None,
            "usdjpy_value": str(row.usdjpy_value) if row.usdjpy_value else None,
            "carry_stress": str(row.carry_stress) if row.carry_stress else None,
        },
        "sub_signal_detail": row.sub_signals,
    }


@router.get("/api/macro/status")
def get_macro_status():
    """Check which macro data sources are configured."""
    return {
        "fred_api_key": bool(settings.fred_api_key),
        "twelve_data_api_key": bool(settings.twelve_data_api_key),
        "eia_api_key": bool(settings.eia_api_key),
        "cftc": True,  # Always available (no key needed)
    }


def _serialize_rows(rows, columns: list[str]) -> list[dict]:
    """Serialize a list of model rows to dicts."""
    result = []
    for r in rows:
        d = {"timestamp": r.timestamp.isoformat()}
        for col in columns:
            val = getattr(r, col, None)
            d[col] = str(val) if val is not None else None
        result.append(d)
    return result


@router.get("/api/macro/oil")
def get_oil_data(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get raw oil price + inventory data."""
    rows = db.execute(
        select(OilData).order_by(OilData.timestamp.desc()).limit(limit)
    ).scalars().all()
    return {
        "count": len(rows),
        "data": _serialize_rows(
            rows, ["wti_price", "brent_price", "wti_brent_spread",
                   "crude_inventory", "inventory_change"]
        ),
    }


@router.get("/api/macro/dollar")
def get_dollar_data(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get raw DXY + VIX data."""
    rows = db.execute(
        select(MacroPrices).order_by(MacroPrices.timestamp.desc()).limit(limit)
    ).scalars().all()
    return {
        "count": len(rows),
        "data": _serialize_rows(rows, ["dxy_index", "vix"]),
    }


@router.get("/api/macro/rates")
def get_rate_data(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get raw treasury yield + rate data."""
    rows = db.execute(
        select(RateData).order_by(RateData.timestamp.desc()).limit(limit)
    ).scalars().all()
    return {
        "count": len(rows),
        "data": _serialize_rows(
            rows, ["dgs2", "dgs10", "yield_curve_2s10s", "dfii10", "t5yie", "cpi_yoy"]
        ),
    }


@router.get("/api/macro/liquidity")
def get_liquidity_data(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get raw M2/Fed balance sheet/liquidity data."""
    rows = db.execute(
        select(LiquidityData).order_by(LiquidityData.timestamp.desc()).limit(limit)
    ).scalars().all()
    return {
        "count": len(rows),
        "data": _serialize_rows(
            rows, ["m2_supply", "fed_balance_sheet", "fed_funds_rate",
                   "treasury_general_acct", "reverse_repo", "net_liquidity"]
        ),
    }


@router.get("/api/macro/carry")
def get_carry_data(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get raw carry trade data."""
    rows = db.execute(
        select(CarryTradeData).order_by(CarryTradeData.timestamp.desc()).limit(limit)
    ).scalars().all()
    return {
        "count": len(rows),
        "data": _serialize_rows(
            rows, ["usdjpy", "eurusd", "usdjpy_sma_20", "usdjpy_atr_14",
                   "usdjpy_rsi_14", "jpy_net_positioning",
                   "jpy_positioning_zscore", "carry_stress_score"]
        ),
    }
