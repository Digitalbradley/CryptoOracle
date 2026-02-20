"""On-chain metrics model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OnchainMetrics(Base):
    __tablename__ = "onchain_metrics"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)

    exchange_inflow: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    exchange_outflow: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))
    exchange_netflow: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 8))

    whale_transactions_count: Mapped[int | None] = mapped_column(Integer)
    whale_volume_usd: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 2))

    active_addresses: Mapped[int | None] = mapped_column(Integer)
    hash_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 4))

    nupl: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6))
    mvrv_zscore: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6))
    sopr: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 6))

    onchain_score: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4))
