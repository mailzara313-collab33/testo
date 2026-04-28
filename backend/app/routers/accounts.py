from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, ManagerOrAdmin
from app.database import get_db
from app.models.account import GoogleAdsAccount
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.google_ads import google_ads_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AccountResponse]:
    result = await db.execute(
        select(GoogleAdsAccount).where(GoogleAdsAccount.is_active == True).order_by(GoogleAdsAccount.name)
    )
    accounts = result.scalars().all()

    # İlk çalıştırmada Google Ads'den otomatik sync
    if not accounts:
        remote = await google_ads_service.list_accounts()
        for acc in remote:
            obj = GoogleAdsAccount(**acc)
            db.add(obj)
        await db.commit()
        result2 = await db.execute(select(GoogleAdsAccount).order_by(GoogleAdsAccount.name))
        accounts = result2.scalars().all()

    return [AccountResponse.model_validate(a) for a in accounts]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> AccountResponse:
    existing = await db.execute(
        select(GoogleAdsAccount).where(GoogleAdsAccount.customer_id == data.customer_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu hesap zaten kayıtlı")
    account = GoogleAdsAccount(**data.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    result = await db.execute(select(GoogleAdsAccount).where(GoogleAdsAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hesap bulunamadı")
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> AccountResponse:
    result = await db.execute(select(GoogleAdsAccount).where(GoogleAdsAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hesap bulunamadı")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.post("/{account_id}/sync")
async def sync_account(
    account_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> dict:
    result = await db.execute(select(GoogleAdsAccount).where(GoogleAdsAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hesap bulunamadı")

    from datetime import datetime, timezone
    account.synced_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": f"{account.name} senkronize edildi", "synced_at": account.synced_at}
