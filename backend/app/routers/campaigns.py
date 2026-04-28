from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, ManagerOrAdmin
from app.database import get_db
from app.models.audit import AuditLog
from app.schemas.campaign import BudgetUpdateRequest, CampaignActionRequest, CampaignSnapshotResponse
from app.services.google_ads import google_ads_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignSnapshotResponse])
async def list_campaigns(
    current_user: CurrentUser,
    account_id: str = Query(..., description="Google Ads müşteri ID"),
    date_from: date = Query(default_factory=lambda: date.today() - timedelta(days=29)),
    date_to: date = Query(default_factory=date.today),
    status_filter: str | None = Query(None, alias="status"),
    campaign_type: str | None = Query(None),
    sort_by: str = Query("cost"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[dict]:
    campaigns = await google_ads_service.list_campaigns(account_id, date_from, date_to)

    if status_filter:
        campaigns = [c for c in campaigns if c["status"] == status_filter.upper()]
    if campaign_type:
        campaigns = [c for c in campaigns if c["campaign_type"] == campaign_type.upper()]

    reverse = sort_dir.lower() == "desc"
    try:
        campaigns.sort(key=lambda c: c.get(sort_by, 0), reverse=reverse)
    except TypeError:
        pass

    start = (page - 1) * page_size
    return campaigns[start : start + page_size]


@router.post("/action")
async def campaign_action(
    data: CampaignActionRequest,
    request: Request,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> dict:
    action = data.action.lower()
    if action not in ("pause", "enable", "remove"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz aksiyon")

    if action == "pause":
        ok = await google_ads_service.pause_campaign(data.account_id, data.campaign_id)
    elif action == "enable":
        ok = await google_ads_service.enable_campaign(data.account_id, data.campaign_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remove işlemi henüz desteklenmiyor. Google Ads arayüzünden yapın.",
        )

    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="İşlem başarısız")

    log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action=f"campaign_{action}",
        resource_type="campaign",
        resource_id=data.campaign_id,
        account_id=data.account_id,
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    await db.commit()

    return {"message": f"Kampanya {action} işlemi başarılı", "campaign_id": data.campaign_id}


@router.post("/budget")
async def update_budget(
    data: BudgetUpdateRequest,
    request: Request,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> dict:
    if data.new_daily_budget <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bütçe 0'dan büyük olmalı")

    ok = await google_ads_service.update_campaign_budget(
        data.account_id, data.campaign_id, data.new_daily_budget
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Bütçe güncellenemedi")

    import json
    log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="budget_update",
        resource_type="campaign",
        resource_id=data.campaign_id,
        account_id=data.account_id,
        details_json=json.dumps({"new_daily_budget": data.new_daily_budget, "reason": data.reason}),
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    await db.commit()

    return {
        "message": "Günlük bütçe güncellendi",
        "campaign_id": data.campaign_id,
        "new_daily_budget": data.new_daily_budget,
    }
