from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.session import UserSession
from app.models.email import Email, EmailStatus, EmailClassification
from app.models.ignore_rule import IgnoreRule, RuleField, MatchType
from app.workers.trigger import trigger_email_processing

router = APIRouter(prefix="/api/triage", tags=["triage"])


class TriageAction(BaseModel):
    action: str  # "import_po", "track_shipment", "ignore", "always_ignore_sender"


@router.get("")
async def list_triage(
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(Email)
        .where(Email.user_id == user.odoo_uid)
        .where(Email.status == EmailStatus.TRIAGE)
        .order_by(Email.created_at.desc())
    )
    emails = result.scalars().all()
    return [
        {
            "id": e.id,
            "sender": e.sender,
            "subject": e.subject,
            "classification": e.classification.value,
            "created_at": e.created_at.isoformat(),
        }
        for e in emails
    ]


@router.post("/{email_id}/action")
async def triage_action(
    email_id: int,
    action: TriageAction,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == user.odoo_uid)
    )
    email_record = result.scalar_one_or_none()
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")

    if action.action == "import_po":
        email_record.classification = EmailClassification.PURCHASE_ORDER
        email_record.status = EmailStatus.PROCESSING
    elif action.action == "track_shipment":
        email_record.classification = EmailClassification.SHIPPING_NOTICE
        email_record.status = EmailStatus.PROCESSING
    elif action.action == "ignore":
        email_record.status = EmailStatus.IGNORED
    elif action.action == "always_ignore_sender":
        email_record.status = EmailStatus.IGNORED
        domain = email_record.sender_domain
        if domain:
            rule = IgnoreRule(
                field=RuleField.DOMAIN,
                match_type=MatchType.EXACT,
                value=domain,
                user_id=user.odoo_uid,
            )
        else:
            rule = IgnoreRule(
                field=RuleField.SENDER,
                match_type=MatchType.EXACT,
                value=email_record.sender,
                user_id=user.odoo_uid,
            )
        db.add(rule)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")

    await db.commit()
    if email_record.status == EmailStatus.PROCESSING:
        await trigger_email_processing()
    return {"status": "ok", "email_id": email_id, "action": action.action}
