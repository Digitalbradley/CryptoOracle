"""Watched symbols configuration model."""

from datetime import datetime

from sqlalchemy import Boolean, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WatchedSymbols(Base):
    __tablename__ = "watched_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(30), default="binance")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timeframes: Mapped[dict] = mapped_column(
        JSON, default=["1h", "4h", "1d"]
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
