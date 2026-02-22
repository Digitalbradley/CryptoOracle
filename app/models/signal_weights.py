"""Signal weight profiles model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SignalWeights(Base):
    __tablename__ = "signal_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_name: Mapped[str] = mapped_column(String(50), default="default")

    ta_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.25)
    onchain_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.20)
    celestial_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.15)
    numerology_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.10)
    sentiment_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.15)
    political_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.15)
    macro_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), default=0.00)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
