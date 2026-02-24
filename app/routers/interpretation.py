"""AI interpretation router — Claude-powered signal analysis."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.interpretation_engine import InterpretationEngine
from app.utils import normalize_symbol

router = APIRouter(tags=["interpretation"])


@router.get("/api/interpretation/{symbol}")
def get_interpretation(
    symbol: str,
    timeframe: str = Query("1h", description="Candle timeframe"),
    db: Session = Depends(get_db),
):
    """Get AI-powered interpretation of current confluence signals.

    Returns a plain-English analysis of what the signals mean together,
    with per-layer insights and a key thing to watch.

    Results are cached for 30 minutes to manage API costs.
    """
    symbol = normalize_symbol(symbol)
    engine = InterpretationEngine()
    return engine.interpret(db, symbol, timeframe)
