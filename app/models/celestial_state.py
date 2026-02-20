"""Celestial/ephemeris state model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DECIMAL, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CelestialState(Base):
    __tablename__ = "celestial_state"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)

    # Lunar
    lunar_phase_angle: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    lunar_phase_name: Mapped[str | None] = mapped_column(String(20))
    lunar_illumination: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
    days_to_next_new_moon: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2))
    days_to_next_full_moon: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2))
    is_lunar_eclipse: Mapped[bool] = mapped_column(Boolean, default=False)
    is_solar_eclipse: Mapped[bool] = mapped_column(Boolean, default=False)

    # Retrogrades
    mercury_retrograde: Mapped[bool] = mapped_column(Boolean, default=False)
    venus_retrograde: Mapped[bool] = mapped_column(Boolean, default=False)
    mars_retrograde: Mapped[bool] = mapped_column(Boolean, default=False)
    jupiter_retrograde: Mapped[bool] = mapped_column(Boolean, default=False)
    saturn_retrograde: Mapped[bool] = mapped_column(Boolean, default=False)
    retrograde_count: Mapped[int] = mapped_column(Integer, default=0)

    # Planetary positions
    sun_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    moon_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    mercury_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    venus_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    mars_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    jupiter_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))
    saturn_longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4))

    # Aspects and ingresses
    active_aspects: Mapped[dict | None] = mapped_column(JSON, default=list)
    ingresses: Mapped[dict | None] = mapped_column(JSON, default=list)

    # Composite
    celestial_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
