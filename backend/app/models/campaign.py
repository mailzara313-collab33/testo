from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CampaignSnapshot(Base):
    """Günlük kampanya performans verisi."""

    __tablename__ = "campaign_snapshots"
    __table_args__ = (
        Index("ix_snapshot_account_date", "account_id", "snapshot_date"),
        Index("ix_snapshot_campaign_date", "campaign_id", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    campaign_name: Mapped[str] = mapped_column(String(500), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Spend metrics (micros → TL converted at write time)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[float] = mapped_column(Float, default=0.0)
    conversion_value: Mapped[float] = mapped_column(Float, default=0.0)

    # Calculated metrics (stored for fast queries)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    cpc: Mapped[float] = mapped_column(Float, default=0.0)
    cpa: Mapped[float] = mapped_column(Float, default=0.0)
    roas: Mapped[float] = mapped_column(Float, default=0.0)

    # Budget
    daily_budget: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Quality
    avg_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_impression_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_lost_is_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_lost_is_rank: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
