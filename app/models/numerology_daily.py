"""Numerology daily state model."""

import datetime as dt
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DECIMAL, Date, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NumerologyDaily(Base):
    __tablename__ = "numerology_daily"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True, unique=True)

    date_digit_sum: Mapped[int | None] = mapped_column(Integer)
    is_master_number: Mapped[bool] = mapped_column(Boolean, default=False)
    master_number_value: Mapped[int | None] = mapped_column(Integer)
    universal_day_number: Mapped[int | None] = mapped_column(Integer)

    active_cycles: Mapped[dict | None] = mapped_column(JSON, default=dict)
    cycle_confluence_count: Mapped[int] = mapped_column(Integer, default=0)

    price_47_appearances: Mapped[dict | None] = mapped_column(JSON, default=list)

    numerology_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
