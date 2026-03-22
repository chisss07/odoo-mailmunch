from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.session import UserSession
from app.models.settings import AppSettings
from app.models.ignore_rule import IgnoreRule, RuleField, MatchType
from app.services.encryption import encrypt, decrypt

router = APIRouter(prefix="/api/settings", tags=["settings"])

SECRET_KEYS = {"m365_client_secret", "m365_tenant_id", "m365_client_id"}


class SettingUpdate(BaseModel):
    key: str
    value: str


class IgnoreRuleCreate(BaseModel):
    field: str
    match_type: str
    value: str


@router.get("")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(select(AppSettings))
    settings_list = result.scalars().all()
    output = {}
    for s in settings_list:
        if s.is_secret:
            output[s.key] = "****" if s.value_encrypted else None
        else:
            output[s.key] = s.value_plain
    return output


@router.put("")
async def update_setting(
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(select(AppSettings).where(AppSettings.key == update.key))
    setting = result.scalar_one_or_none()
    is_secret = update.key in SECRET_KEYS

    if setting is None:
        setting = AppSettings(key=update.key, is_secret=is_secret)
        db.add(setting)

    if is_secret:
        setting.value_encrypted = encrypt(update.value)
        setting.value_plain = None
    else:
        setting.value_plain = update.value
        setting.value_encrypted = None

    setting.is_secret = is_secret
    await db.commit()
    return {"status": "ok"}


@router.get("/ignore-rules")
async def list_ignore_rules(
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(IgnoreRule).where(IgnoreRule.user_id == user.odoo_uid).order_by(IgnoreRule.created_at)
    )
    rules = result.scalars().all()
    return [
        {
            "id": r.id,
            "field": r.field.value,
            "match_type": r.match_type.value,
            "value": r.value,
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ]


@router.post("/ignore-rules")
async def create_ignore_rule(
    rule: IgnoreRuleCreate,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    try:
        field_enum = RuleField(rule.field)
        match_type_enum = MatchType(rule.match_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_rule = IgnoreRule(
        field=field_enum,
        match_type=match_type_enum,
        value=rule.value,
        user_id=user.odoo_uid,
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return {"id": new_rule.id, "status": "created"}


@router.delete("/ignore-rules/{rule_id}")
async def delete_ignore_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(IgnoreRule).where(IgnoreRule.id == rule_id, IgnoreRule.user_id == user.odoo_uid)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted"}
