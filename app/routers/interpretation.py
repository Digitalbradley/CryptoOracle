"""AI interpretation router — Claude-powered signal analysis."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.interpretation_engine import InterpretationEngine
from app.utils import normalize_symbol

router = APIRouter(tags=["interpretation"])


# ---------------------------------------------------------------------------
# GET — interpretation (with optional force refresh)
# ---------------------------------------------------------------------------

@router.get("/api/interpretation/{symbol}")
def get_interpretation(
    symbol: str,
    timeframe: str = Query("1h", description="Candle timeframe"),
    force: bool = Query(False, description="Bypass cache and generate fresh analysis"),
    db: Session = Depends(get_db),
):
    """Get AI-powered interpretation of current confluence signals.

    Returns a plain-English analysis of what the signals mean together,
    with per-layer insights and a key thing to watch.

    Results are cached for 30 minutes. Pass ``force=true`` to bypass the cache.
    """
    symbol = normalize_symbol(symbol)
    engine = InterpretationEngine()
    return engine.interpret(db, symbol, timeframe, force=force)


# ---------------------------------------------------------------------------
# POST — chat follow-up
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    timeframe: str = "1h"


@router.post("/api/interpretation/{symbol}/chat")
def chat_with_signals(
    symbol: str,
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    """Ask follow-up questions about a symbol's signals.

    The full 7-layer signal context is injected as system context so Claude
    can reference actual numbers in its answers.
    """
    symbol = normalize_symbol(symbol)
    engine = InterpretationEngine()

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    response_text = engine.chat(db, symbol, body.timeframe, messages)

    return {
        "response": response_text,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
