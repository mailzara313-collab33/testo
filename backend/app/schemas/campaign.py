from datetime import date, datetime

from pydantic import BaseModel


class CampaignSnapshotResponse(BaseModel):
    id: int
    account_id: str
    campaign_id: str
    campaign_name: str
    campaign_type: str
    status: str
    snapshot_date: date
    cost: float
    impressions: int
    clicks: int
    conversions: float
    conversion_value: float
    ctr: float
    cpc: float
    cpa: float
    roas: float
    daily_budget: float | None
    avg_quality_score: float | None

    model_config = {"from_attributes": True}


class CampaignActionRequest(BaseModel):
    campaign_id: str
    account_id: str
    action: str  # "pause" | "enable" | "remove"


class BudgetUpdateRequest(BaseModel):
    campaign_id: str
    account_id: str
    new_daily_budget: float
    reason: str | None = None


class CampaignListParams(BaseModel):
    account_id: str | None = None
    status: str | None = None
    campaign_type: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    sort_by: str = "cost"
    sort_dir: str = "desc"
    page: int = 1
    page_size: int = 50
