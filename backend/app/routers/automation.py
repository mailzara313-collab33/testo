import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, ManagerOrAdmin
from app.database import get_db
from app.models.automation import Alert, AutomationLog, AutomationRule, RuleStatus
from app.schemas.dashboard import AlertSchema, AutomationRuleSchema

router = APIRouter(prefix="/automation", tags=["automation"])

RULE_TEMPLATES = [
    {
        "name": "Düşük ROAS Kampanya Durdur",
        "description": "ROAS < 2.0 olan kampanyaları duraklat (manuel onaylı)",
        "condition_json": json.dumps({"metric": "roas", "operator": "<", "value": 2.0}),
        "action_json": json.dumps({"action": "pause_campaign", "require_approval": True}),
        "schedule": "0 8 * * *",
    },
    {
        "name": "Bütçe %95 Uyarı",
        "description": "Günlük bütçenin %95'i kullanıldığında uyarı gönder",
        "condition_json": json.dumps({"metric": "budget_pct_used", "operator": ">=", "value": 95}),
        "action_json": json.dumps({"action": "send_alert", "severity": "warning"}),
        "schedule": "*/30 * * * *",
    },
    {
        "name": "Yüksek CPA Teklif Düşür",
        "description": "CPA hedefin %50 üstünde 3 gündür ise teklif -%10",
        "condition_json": json.dumps(
            {"metric": "cpa", "operator": ">", "value": "target_cpa * 1.5", "consecutive_days": 3}
        ),
        "action_json": json.dumps({"action": "adjust_bid", "change_pct": -10}),
        "schedule": "0 9 * * *",
    },
    {
        "name": "0 Dönüşüm + 100 Tıklama Durdur",
        "description": "Dönüşüm yok ama 100+ tıklama olan kampanyaları duraklat",
        "condition_json": json.dumps(
            {"conditions": [{"metric": "conversions", "operator": "=", "value": 0},
                            {"metric": "clicks", "operator": ">=", "value": 100}]}
        ),
        "action_json": json.dumps({"action": "pause_campaign"}),
        "schedule": "0 10 * * *",
    },
    {
        "name": "Gece Saatleri Teklif Azalt",
        "description": "23:00 - 06:00 arası düşük performanslı saatlerde teklif -%30",
        "condition_json": json.dumps({"hour_range": {"from": 23, "to": 6}}),
        "action_json": json.dumps({"action": "adjust_bid", "change_pct": -30}),
        "schedule": "0 23 * * *",
    },
]


@router.get("/rules", response_model=list[AutomationRuleSchema])
async def list_rules(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: str | None = Query(None),
) -> list[AutomationRuleSchema]:
    query = select(AutomationRule).order_by(AutomationRule.created_at.desc())
    if account_id:
        query = query.where(AutomationRule.account_id == account_id)
    result = await db.execute(query)
    return [AutomationRuleSchema.model_validate(r) for r in result.scalars().all()]


@router.post("/rules/seed-templates")
async def seed_templates(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> dict:
    for tmpl in RULE_TEMPLATES:
        rule = AutomationRule(**tmpl, created_by=current_user.id, is_dry_run=True)
        db.add(rule)
    await db.commit()
    return {"message": f"{len(RULE_TEMPLATES)} kural şablonu oluşturuldu"}


@router.post("/rules", response_model=AutomationRuleSchema, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: AutomationRuleSchema,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> AutomationRuleSchema:
    rule = AutomationRule(
        name=data.name,
        description=data.description,
        status=RuleStatus.draft,
        is_dry_run=data.is_dry_run,
        condition_json=data.condition_json,
        action_json=data.action_json,
        schedule=data.schedule,
        created_by=current_user.id,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return AutomationRuleSchema.model_validate(rule)


@router.patch("/rules/{rule_id}/status")
async def toggle_rule(
    rule_id: int,
    body: dict,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated = ManagerOrAdmin,
) -> dict:
    result = await db.execute(select(AutomationRule).where(AutomationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kural bulunamadı")

    new_status = body.get("status", "paused")
    rule.status = RuleStatus(new_status)
    await db.commit()
    return {"message": f"Kural durumu: {new_status}", "rule_id": rule_id}


@router.get("/logs", response_model=list[dict])
async def list_logs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    rule_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    query = select(AutomationLog).order_by(AutomationLog.created_at.desc()).limit(limit)
    if rule_id:
        query = query.where(AutomationLog.rule_id == rule_id)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "rule_id": log.rule_id,
            "action_taken": log.action_taken,
            "dry_run": log.dry_run,
            "success": log.success,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/alerts", response_model=list[AlertSchema])
async def list_alerts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = Query(False),
    account_id: str | None = Query(None),
) -> list[AlertSchema]:
    query = select(Alert).order_by(Alert.created_at.desc()).limit(100)
    if unread_only:
        query = query.where(Alert.is_read == False)
    if account_id:
        query = query.where(Alert.account_id == account_id)
    result = await db.execute(query)
    return [AlertSchema.model_validate(a) for a in result.scalars().all()]


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uyarı bulunamadı")
    alert.is_read = True
    await db.commit()
    return {"message": "Uyarı okundu olarak işaretlendi"}
