"""Alerts model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Alerts(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    triggered_at: Mapped[datetime | None]
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    trigger_data: Mapped[dict | None] = mapped_column(JSON)
    composite_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    aligned_layers: Mapped[dict | None] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(String(20), default="active")
    acknowledged_at: Mapped[datetime | None]
