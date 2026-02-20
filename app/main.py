"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("CryptoOracle starting up (env=%s)", settings.app_env)
    yield
    logger.info("CryptoOracle shutting down")


app = FastAPI(
    title="CryptoOracle",
    description="Esoteric Crypto Trading Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
