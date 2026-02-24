"""FastAPI application entry point."""

import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse, JSONResponse

from app.config import settings
from app.database import SessionLocal, get_db
from app.routers import health
from app.routers import price
from app.routers import signals
from app.routers import celestial
from app.routers import numerology
from app.routers import sentiment
from app.routers import onchain
from app.routers import confluence
from app.routers import alerts_router
from app.routers import backtest
from app.routers import political
from app.routers import macro
from app.routers import auth
from app.routers import interpretation
from app.services.auth_service import decode_access_token, ensure_admin_user
from app.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Paths that do not require authentication
# ---------------------------------------------------------------------------
PUBLIC_PATHS = {
    "/health",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/me",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Global JWT authentication middleware.

    Reads the ``access_token`` httpOnly cookie.  Protected paths return 401
    if the cookie is missing or the token is invalid/expired.  Public paths
    are always allowed through, but the token is still decoded when present
    so ``request.state.user`` is available on public endpoints like ``/api/auth/me``.
    """

    async def dispatch(self, request, call_next):
        # Always allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        token = request.cookies.get("access_token")

        # Attempt to decode the token (used for both public and protected paths)
        username = None
        if token:
            username = decode_access_token(token)

        if username:
            request.state.user = username

        # Public paths — allow through regardless of auth state
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Static files and SPA routes — allow through (auth handled client-side)
        if not path.startswith("/api/"):
            return await call_next(request)

        # Protected API paths — require valid token
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        if not username:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("CryptoOracle starting up (env=%s)", settings.app_env)

    # Seed admin user from env vars if no users exist
    db = SessionLocal()
    try:
        ensure_admin_user(db)
    finally:
        db.close()

    start_scheduler()
    yield
    stop_scheduler()
    logger.info("CryptoOracle shutting down")


BUILD_TIMESTAMP = "2026-02-22T20:00:00Z"

app = FastAPI(
    title="CryptoOracle",
    description="Esoteric Crypto Trading Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware (Starlette applies in reverse order — CORS must wrap auth)
# ---------------------------------------------------------------------------
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(price.router)
app.include_router(signals.router)
app.include_router(celestial.router)
app.include_router(numerology.router)
app.include_router(sentiment.router)
app.include_router(onchain.router)
app.include_router(confluence.router)
app.include_router(alerts_router.router)
app.include_router(backtest.router)
app.include_router(political.router)
app.include_router(macro.router)
app.include_router(interpretation.router)


@app.post("/api/bootstrap", tags=["admin"])
def bootstrap(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger the initial data backfill and TA computation.

    Runs synchronously — can take 10-20 minutes for large backfills.
    Monitor progress via server logs.
    """
    try:
        from app.services.seed import run_bootstrap

        result = run_bootstrap(db)
        return {"status": "complete", **result}
    except Exception as e:
        logger.exception("Phase 1 bootstrap failed")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/bootstrap/phase2", tags=["admin"])
def bootstrap_phase2(db: Session = Depends(get_db)):
    """Trigger Phase 2 bootstrap: seed gematria, 47-day cycle, backfill celestial + numerology.

    This can take several minutes for the full date range backfill.
    Monitor progress via server logs.
    """
    try:
        from app.services.phase2_seed import run_phase2_bootstrap

        result = run_phase2_bootstrap(db)
        return {"status": "complete", **result}
    except Exception as e:
        logger.exception("Phase 2 bootstrap failed")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/migrate", tags=["admin"])
def run_migrations():
    """Run pending Alembic migrations."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        return {"status": "complete", "message": "Migrations applied successfully"}
    except Exception as e:
        logger.exception("Migration failed")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/bootstrap/phase3", tags=["admin"])
def bootstrap_phase3(db: Session = Depends(get_db)):
    """Trigger Phase 3 bootstrap: seed weights, backfill sentiment, compute confluence, run backtest.

    This can take several minutes depending on data volume.
    Monitor progress via server logs.
    """
    try:
        from app.services.phase3_seed import run_phase3_bootstrap

        result = run_phase3_bootstrap(db)
        return {"status": "complete", **result}
    except Exception as e:
        logger.exception("Phase 3 bootstrap failed")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/bootstrap/phase4", tags=["admin"])
def bootstrap_phase4(db: Session = Depends(get_db)):
    """Trigger Phase 4 bootstrap: seed political calendar, fetch initial news, compute signal.

    Requires no API keys for basic operation (RSS feeds).
    NewsAPI/GNews/Claude classification require respective API keys.
    Monitor progress via server logs.
    """
    try:
        from app.services.phase4_seed import run_phase4_bootstrap

        result = run_phase4_bootstrap(db)
        return {"status": "complete", **result}
    except Exception as e:
        logger.exception("Phase 4 bootstrap failed")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/bootstrap/phase5", tags=["admin"])
def bootstrap_phase5(db: Session = Depends(get_db)):
    """Trigger Phase 5 bootstrap: Macro Liquidity (Layer 7).

    Backfills FRED (1yr), forex (90d), CFTC COT (52wk), EIA (2yr),
    seeds weight profile, adds macro calendar events, computes initial signal.
    Requires FRED_API_KEY at minimum. Optional: TWELVE_DATA_API_KEY, EIA_API_KEY.
    """
    try:
        from app.services.phase5_seed import run_phase5_bootstrap

        result = run_phase5_bootstrap(db)
        return {"status": "complete", **result}
    except Exception as e:
        logger.exception("Phase 5 bootstrap failed")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


# ---------------------------------------------------------------------------
# Serve frontend static files (built by Vite into frontend/dist)
# ---------------------------------------------------------------------------
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
logger.info("Frontend dist path: %s (exists=%s)", FRONTEND_DIST, FRONTEND_DIST.is_dir())

if FRONTEND_DIST.is_dir():
    # Mount static assets (JS, CSS, images) under /assets
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA index.html for all non-API, non-asset routes."""
        # Try to serve a static file first (e.g. favicon.ico)
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for client-side routing
        return FileResponse(str(FRONTEND_DIST / "index.html"))
