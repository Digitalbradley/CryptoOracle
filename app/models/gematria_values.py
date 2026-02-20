"""Gematria reference values model."""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GematriaValues(Base):
    __tablename__ = "gematria_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    english_ordinal: Mapped[int | None] = mapped_column(Integer)
    full_reduction: Mapped[int | None] = mapped_column(Integer)
    reverse_ordinal: Mapped[int | None] = mapped_column(Integer)
    reverse_reduction: Mapped[int | None] = mapped_column(Integer)
    jewish_gematria: Mapped[int | None] = mapped_column(Integer)
    english_gematria: Mapped[int | None] = mapped_column(Integer)

    digit_sum: Mapped[int | None] = mapped_column(Integer)
    is_prime: Mapped[bool | None] = mapped_column(Boolean)
    associated_planet: Mapped[str | None] = mapped_column(String(20))
    associated_element: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
