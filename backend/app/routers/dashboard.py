from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser
from app.schemas.dashboard import (
    CampaignSpendShare,
    DashboardKPIs,
    DashboardResponse,
    HeatmapCell,
    KPIData,
    TimeSeriesPoint,
)
from app.services.google_ads import google_ads_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _kpi(current: float, previous: float) -> KPIData:
    if previous:
        change_pct = round((current - previous) / previous * 100, 1)
    else:
        change_pct = 0.0
    return KPIData(value=round(current, 2), previous_value=round(previous, 2), change_pct=change_pct)


def _aggregate(campaigns: list[dict]) -> dict:
    cost = sum(c["cost"] for c in campaigns)
    clicks = sum(c["clicks"] for c in campaigns)
    impressions = sum(c["impressions"] for c in campaigns)
    conversions = sum(c["conversions"] for c in campaigns)
    conv_value = sum(c["conversion_value"] for c in campaigns)
    ctr = clicks / impressions * 100 if impressions else 0
    cpc = cost / clicks if clicks else 0
    cpa = cost / conversions if conversions else 0
    roas = conv_value / cost if cost else 0
    return dict(
        cost=cost, clicks=clicks, impressions=impressions,
        conversions=conversions, conv_value=conv_value,
        ctr=ctr, cpc=cpc, cpa=cpa, roas=roas,
    )


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: CurrentUser,
    account_id: str | None = Query(None),
    date_from: date = Query(default_factory=lambda: date.today() - timedelta(days=29)),
    date_to: date = Query(default_factory=date.today),
) -> DashboardResponse:
    effective_account = account_id or "1234567890"
    days = (date_to - date_from).days + 1

    # Current period
    campaigns = await google_ads_service.list_campaigns(effective_account, date_from, date_to)
    curr = _aggregate(campaigns)

    # Previous period (same length)
    prev_to = date_from - timedelta(days=1)
    prev_from = prev_to - timedelta(days=days - 1)
    prev_campaigns = await google_ads_service.list_campaigns(effective_account, prev_from, prev_to)
    prev = _aggregate(prev_campaigns)

    kpis = DashboardKPIs(
        cost=_kpi(curr["cost"], prev["cost"]),
        conversions=_kpi(curr["conversions"], prev["conversions"]),
        conversion_value=_kpi(curr["conv_value"], prev["conv_value"]),
        roas=_kpi(curr["roas"], prev["roas"]),
        cpa=_kpi(curr["cpa"], prev["cpa"]),
        ctr=_kpi(curr["ctr"], prev["ctr"]),
        cpc=_kpi(curr["cpc"], prev["cpc"]),
        impressions=_kpi(curr["impressions"], prev["impressions"]),
        clicks=_kpi(curr["clicks"], prev["clicks"]),
    )

    # Time series
    raw_series = await google_ads_service.get_time_series(effective_account, date_from, date_to)
    time_series = [
        TimeSeriesPoint(
            date=p["date"],
            cost=p["cost"],
            conversions=p["conversions"],
            clicks=p["clicks"],
            impressions=p["impressions"],
            roas=p["roas"],
        )
        for p in raw_series
    ]

    # Campaign spend share (top 8)
    total_cost = curr["cost"] or 1
    sorted_campaigns = sorted(campaigns, key=lambda c: c["cost"], reverse=True)[:8]
    spend_by_campaign = [
        CampaignSpendShare(
            campaign_name=c["campaign_name"],
            campaign_id=c["campaign_id"],
            cost=round(c["cost"], 2),
            pct=round(c["cost"] / total_cost * 100, 1),
        )
        for c in sorted_campaigns
    ]

    # Heatmap
    raw_heatmap = await google_ads_service.get_hourly_heatmap(effective_account)
    heatmap = [HeatmapCell(**cell) for cell in raw_heatmap]

    return DashboardResponse(
        kpis=kpis,
        time_series=time_series,
        spend_by_campaign=spend_by_campaign,
        hourly_heatmap=heatmap,
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
    )
