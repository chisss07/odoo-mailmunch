import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, get_odoo_client
from app.models.session import UserSession
from app.models.po_tracking import POTracking
from app.services.odoo_client import OdooClient
from app.services.po_builder import create_receipt_in_odoo

router = APIRouter(prefix="/api/pos", tags=["purchase_orders"])


class ReceiveRequest(BaseModel):
    lines: list[dict] | None = None


@router.get("/")
async def list_pos(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    query = select(POTracking).where(POTracking.user_id == user.odoo_uid)
    if status:
        query = query.where(POTracking.status == status)
    query = query.order_by(POTracking.created_at.desc())
    result = await db.execute(query)
    pos = result.scalars().all()
    return [
        {
            "id": po.id,
            "odoo_po_id": po.odoo_po_id,
            "odoo_po_name": po.odoo_po_name,
            "vendor_name": po.vendor_name,
            "status": po.status,
            "sales_order_name": po.sales_order_name,
            "tracking_info": json.loads(po.tracking_info) if po.tracking_info else None,
            "created_at": po.created_at.isoformat(),
        }
        for po in pos
    ]


@router.get("/{po_id}")
async def get_po(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
):
    result = await db.execute(
        select(POTracking).where(POTracking.id == po_id, POTracking.user_id == user.odoo_uid)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    return {
        "id": po.id,
        "odoo_po_id": po.odoo_po_id,
        "odoo_po_name": po.odoo_po_name,
        "vendor_name": po.vendor_name,
        "status": po.status,
        "sales_order_id": po.sales_order_id,
        "sales_order_name": po.sales_order_name,
        "tracking_info": json.loads(po.tracking_info) if po.tracking_info else None,
        "last_synced": po.last_synced.isoformat(),
    }


@router.post("/{po_id}/receive")
async def receive_po(
    po_id: int,
    req: ReceiveRequest,
    db: AsyncSession = Depends(get_db),
    user: UserSession = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    result = await db.execute(
        select(POTracking).where(POTracking.id == po_id, POTracking.user_id == user.odoo_uid)
    )
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    try:
        receipt = await create_receipt_in_odoo(odoo, po.odoo_po_id, req.lines)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {str(e)}")
    po.status = "received" if req.lines is None else "partial"
    await db.commit()
    return {"status": po.status, "picking_name": receipt["picking_name"]}
