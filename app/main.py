"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers import health
from app.routers import price
from app.routers import signals
from app.routers import celestial
from app.routers import numerology
from app.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("CryptoOracle starting up (env=%s)", settings.app_env)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("CryptoOracle shutting down")


app = FastAPI(
    title="CryptoOracle",
    description="Esoteric Crypto Trading Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(price.router)
app.include_router(signals.router)
app.include_router(celestial.router)
app.include_router(numerology.router)


@app.post("/api/bootstrap", tags=["admin"])
def bootstrap(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger the initial data backfill and TA computation.

    Runs in the background so the request returns immediately.
    Monitor progress via server logs.
    """
    from app.services.seed import run_bootstrap

    # Run bootstrap synchronously for now — the HTTP request will block
    # until complete. For large backfills this can take 10-20 minutes.
    # A future improvement would be to run this as a background task.
    result = run_bootstrap(db)
    return {"status": "complete", **result}


@app.post("/api/bootstrap/phase2", tags=["admin"])
def bootstrap_phase2(db: Session = Depends(get_db)):
    """Trigger Phase 2 bootstrap: seed gematria, 47-day cycle, backfill celestial + numerology.

    This can take several minutes for the full date range backfill.
    Monitor progress via server logs.
    """
    from app.services.phase2_seed import run_phase2_bootstrap

    result = run_phase2_bootstrap(db)
    return {"status": "complete", **result}
