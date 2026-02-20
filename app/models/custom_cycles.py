"""Custom numeric cycle tracking model."""

import datetime as dt
from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, Date, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CustomCycles(Base):
    __tablename__ = "custom_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cycle_days: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    reference_event: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    miss_count: Mapped[int] = mapped_column(Integer, default=0)
    hit_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    tolerance_days: Mapped[int] = mapped_column(Integer, default=2)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())
