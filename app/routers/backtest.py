"""Backtester API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.backtester import CycleBacktester, SignalBacktester

router = APIRouter(tags=["backtest"])


class CycleBacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    min_magnitude: float = -10.0


class SignalBacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1d"
    start: date | None = None
    end: date | None = None


class OptimizeRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "1d"


@router.post("/api/backtest/cycle")
def run_cycle_backtest(
    body: CycleBacktestRequest,
    db: Session = Depends(get_db),
):
    """Run the 47-day crash cycle backtester.

    Returns a full statistical report with chi-squared analysis,
    celestial cross-reference, and numerology cross-reference.
    """
    backtester = CycleBacktester()
    report = backtester.generate_report(
        db,
        symbol=body.symbol,
        min_magnitude=body.min_magnitude,
    )
    return {"status": "complete", "report": report}


@router.post("/api/backtest/signals")
def run_signal_backtest(
    body: SignalBacktestRequest,
    db: Session = Depends(get_db),
):
    """Run the general signal backtester.

    Replays historical data, computes what confluence scores would have been,
    and measures accuracy against actual price movements.
    """
    backtester = SignalBacktester()
    predictions = backtester.replay_historical(
        db,
        symbol=body.symbol,
        timeframe=body.timeframe,
        start=body.start,
        end=body.end,
    )
    accuracy = backtester.compute_accuracy(predictions)

    return {
        "status": "complete",
        "symbol": body.symbol,
        "timeframe": body.timeframe,
        "total_days_replayed": len(predictions),
        "accuracy": accuracy,
    }


@router.post("/api/backtest/optimize")
def run_weight_optimizer(
    body: OptimizeRequest,
    db: Session = Depends(get_db),
):
    """Run weight optimizer via grid search.

    Tests weight combinations and returns the one with the best 7-day hit rate.
    """
    backtester = SignalBacktester()
    result = backtester.optimize_weights(
        db,
        symbol=body.symbol,
        timeframe=body.timeframe,
    )
    return {"status": "complete", **result}
