from fastapi import APIRouter, Depends, Query
from app.deps import get_current_user, get_odoo_client
from app.models.session import UserSession
from app.services.odoo_client import OdooClient

router = APIRouter(prefix="/api/odoo", tags=["odoo"])


@router.get("/products")
async def search_products(
    q: str = Query(""),
    limit: int = Query(50, le=200),
    odoo: OdooClient = Depends(get_odoo_client),
    user: UserSession = Depends(get_current_user),
):
    domain = []
    if q:
        domain = ["|", "|", ["name", "ilike", q], ["default_code", "ilike", q], ["description", "ilike", q]]
    return await odoo.search_read("product.product", domain, ["name", "default_code", "list_price", "description"], limit=limit)


@router.get("/vendors")
async def search_vendors(
    q: str = Query(""),
    limit: int = Query(50, le=200),
    odoo: OdooClient = Depends(get_odoo_client),
    user: UserSession = Depends(get_current_user),
):
    domain: list = [["supplier_rank", ">", 0]]
    if q:
        domain.append(["name", "ilike", q])
    return await odoo.search_read("res.partner", domain, ["name", "email", "phone"], limit=limit)


@router.get("/sales-orders")
async def search_sales_orders(
    q: str = Query(""),
    limit: int = Query(50, le=200),
    odoo: OdooClient = Depends(get_odoo_client),
    user: UserSession = Depends(get_current_user),
):
    domain: list = [["state", "in", ["sale", "done"]]]
    if q:
        domain = ["|", ["name", "ilike", q], ["partner_id.name", "ilike", q]] + domain
    return await odoo.search_read("sale.order", domain, ["name", "partner_id", "date_order", "amount_total", "state"], limit=limit)
