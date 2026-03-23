import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, get_odoo_client
from app.models.session import UserSession
from app.models.po_draft import PODraft, DraftStatus
from app.models.po_tracking import POTracking, POStatus
from app.services.odoo_client import OdooClient
from app.services.po_builder import create_po_in_odoo

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


class DraftUpdate(BaseModel):
    vendor_odoo_id: int | None = None
    vendor_name: str | None = None
    line_items: list[dict] | None = None
    sales_order_id: int | None = None
    sales_order_name: str | None = None


@router.get("")
async def list_drafts(
    email_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    query = select(PODraft).where(PODraft.user_id == user.odoo_uid, PODraft.status == DraftStatus.DRAFT)
    if email_id is not None:
        query = query.where(PODraft.email_id == email_id)
    query = query.order_by(PODraft.created_at.desc())
    result = await db.execute(query)
    drafts = result.scalars().all()
    return [
        {
            "id": d.id,
            "vendor_name": d.vendor_name,
            "vendor_confidence": d.vendor_confidence,
            "line_items": json.loads(d.line_items) if d.line_items else [],
            "sales_order_name": d.sales_order_name,
            "status": d.status.value,
            "created_at": d.created_at.isoformat(),
        }
        for d in drafts
    ]


@router.get("/{draft_id}")
async def get_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(PODraft).where(PODraft.id == draft_id, PODraft.user_id == user.odoo_uid)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {
        "id": draft.id,
        "email_id": draft.email_id,
        "vendor_odoo_id": draft.vendor_odoo_id,
        "vendor_name": draft.vendor_name,
        "vendor_confidence": draft.vendor_confidence,
        "line_items": json.loads(draft.line_items) if draft.line_items else [],
        "total_amount": draft.total_amount,
        "expected_date": draft.expected_date,
        "sales_order_id": draft.sales_order_id,
        "sales_order_name": draft.sales_order_name,
        "status": draft.status.value,
    }


@router.put("/{draft_id}")
async def update_draft(
    draft_id: int,
    update: DraftUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(PODraft).where(PODraft.id == draft_id, PODraft.user_id == user.odoo_uid)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if update.vendor_odoo_id is not None:
        draft.vendor_odoo_id = update.vendor_odoo_id
    if update.vendor_name is not None:
        draft.vendor_name = update.vendor_name
    if update.line_items is not None:
        draft.line_items = json.dumps(update.line_items)
    if update.sales_order_id is not None:
        draft.sales_order_id = update.sales_order_id
    if update.sales_order_name is not None:
        draft.sales_order_name = update.sales_order_name
    await db.commit()
    await db.refresh(draft)
    return {
        "id": draft.id,
        "email_id": draft.email_id,
        "vendor_odoo_id": draft.vendor_odoo_id,
        "vendor_name": draft.vendor_name,
        "vendor_confidence": draft.vendor_confidence,
        "line_items": json.loads(draft.line_items) if draft.line_items else [],
        "total_amount": draft.total_amount,
        "expected_date": draft.expected_date,
        "sales_order_id": draft.sales_order_id,
        "sales_order_name": draft.sales_order_name,
        "status": draft.status.value,
    }


@router.post("/{draft_id}/submit")
async def submit_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    result = await db.execute(
        select(PODraft).where(PODraft.id == draft_id, PODraft.user_id == user.odoo_uid)
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    line_items = json.loads(draft.line_items) if draft.line_items else []
    if not (draft.vendor_odoo_id or draft.vendor_name) or not line_items:
        raise HTTPException(status_code=400, detail="Draft must have a vendor and at least one line item")
    try:
        po_result = await create_po_in_odoo(odoo, {
            "vendor_odoo_id": draft.vendor_odoo_id,
            "line_items": line_items,
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {str(e)}")
    draft.status = DraftStatus.SUBMITTED
    tracking = POTracking(
        odoo_po_id=po_result["id"],
        odoo_po_name=po_result["name"],
        vendor_name=draft.vendor_name,
        status=POStatus.ordered,
        sales_order_id=draft.sales_order_id,
        sales_order_name=draft.sales_order_name,
        draft_id=draft.id,
        user_id=user.odoo_uid,
    )
    db.add(tracking)
    await db.commit()
    return {"status": "created", "po_id": po_result["id"], "po_name": po_result["name"]}
