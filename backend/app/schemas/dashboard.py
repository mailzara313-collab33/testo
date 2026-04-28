from datetime import date

from pydantic import BaseModel


class KPIData(BaseModel):
    value: float
    previous_value: float
    change_pct: float


class DashboardKPIs(BaseModel):
    cost: KPIData
    conversions: KPIData
    conversion_value: KPIData
    roas: KPIData
    cpa: KPIData
    ctr: KPIData
    cpc: KPIData
    impressions: KPIData
    clicks: KPIData


class TimeSeriesPoint(BaseModel):
    date: date
    cost: float
    conversions: float
    clicks: int
    impressions: int
    roas: float


class CampaignSpendShare(BaseModel):
    campaign_name: str
    campaign_id: str
    cost: float
    pct: float


class HeatmapCell(BaseModel):
    day: int    # 0=Mon … 6=Sun
    hour: int   # 0–23
    value: float


class DashboardResponse(BaseModel):
    kpis: DashboardKPIs
    time_series: list[TimeSeriesPoint]
    spend_by_campaign: list[CampaignSpendShare]
    hourly_heatmap: list[HeatmapCell]
    date_from: date
    date_to: date
    account_id: str | None


class AutomationRuleSchema(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    is_dry_run: bool
    condition_json: str
    action_json: str
    schedule: str
    run_count: int

    model_config = {"from_attributes": True}


class AlertSchema(BaseModel):
    id: int
    account_id: str | None
    campaign_id: str | None
    severity: str
    title: str
    message: str
    is_read: bool

    model_config = {"from_attributes": True}
