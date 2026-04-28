from datetime import datetime

from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: int
    customer_id: str
    name: str
    manager_customer_id: str | None
    currency_code: str
    time_zone: str
    is_manager: bool
    is_active: bool
    label: str | None
    monthly_budget_limit: int | None
    synced_at: datetime | None

    model_config = {"from_attributes": True}


class AccountCreate(BaseModel):
    customer_id: str
    name: str
    manager_customer_id: str | None = None
    currency_code: str = "TRY"
    time_zone: str = "Europe/Istanbul"
    is_manager: bool = False
    label: str | None = None
    monthly_budget_limit: int | None = None


class AccountUpdate(BaseModel):
    name: str | None = None
    label: str | None = None
    notes: str | None = None
    monthly_budget_limit: int | None = None
    is_active: bool | None = None
