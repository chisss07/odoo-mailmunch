import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session
from app.models.session import UserSession
from app.models.po_tracking import POTracking, POStatus
from app.models.cache import ProductCache, VendorCache
from app.services.encryption import decrypt
from app.services.odoo_client import OdooClient, OdooSessionExpired

logger = logging.getLogger(__name__)


async def sync_po_statuses(ctx: dict):
    """Sync PO statuses from Odoo."""
    async with async_session() as db:
        # Get active sessions
        result = await db.execute(select(UserSession))
        sessions = result.scalars().all()

        for session in sessions:
            try:
                odoo_session = decrypt(session.odoo_session_encrypted)
                client = OdooClient(
                    url=session.odoo_url, db=session.odoo_db,
                    uid=session.odoo_uid, session_id=odoo_session,
                )

                # Get open POs for this user
                po_result = await db.execute(
                    select(POTracking)
                    .where(POTracking.user_id == session.odoo_uid)
                    .where(POTracking.status.not_in([POStatus.received, POStatus.cancelled]))
                )
                pos = po_result.scalars().all()

                for po in pos:
                    odoo_pos = await client.search_read(
                        "purchase.order",
                        [["id", "=", po.odoo_po_id]],
                        ["state", "receipt_status"],
                    )
                    if odoo_pos:
                        odoo_po = odoo_pos[0]
                        if odoo_po.get("receipt_status") == "full":
                            po.status = POStatus.received
                        elif odoo_po.get("receipt_status") == "partial":
                            po.status = POStatus.partial
                        elif odoo_po.get("state") == "cancel":
                            po.status = POStatus.cancelled
                        po.last_synced = datetime.now(timezone.utc)

                await client.close()

            except OdooSessionExpired:
                logger.warning(f"Odoo session expired for user {session.odoo_uid}")
            except Exception as e:
                logger.error(f"Sync error for user {session.odoo_uid}: {e}")

        await db.commit()


async def refresh_caches(ctx: dict):
    """Refresh product and vendor caches from Odoo."""
    async with async_session() as db:
        result = await db.execute(select(UserSession))
        sessions = result.scalars().all()

        for session in sessions:
            try:
                odoo_session = decrypt(session.odoo_session_encrypted)
                client = OdooClient(
                    url=session.odoo_url, db=session.odoo_db,
                    uid=session.odoo_uid, session_id=odoo_session,
                )

                # Refresh products
                products = await client.search_read(
                    "product.product", [],
                    ["name", "default_code", "description"],
                    limit=5000,
                )
                now = datetime.now(timezone.utc)

                # Bulk-load existing cache for O(1) lookups
                existing_products_result = await db.execute(select(ProductCache))
                product_cache_map = {pc.odoo_id: pc for pc in existing_products_result.scalars().all()}

                for p in products:
                    cached = product_cache_map.get(p["id"])
                    if cached:
                        cached.name = p["name"]
                        cached.default_code = p.get("default_code") or None
                        cached.description = p.get("description") or None
                        cached.last_refreshed = now
                    else:
                        db.add(ProductCache(
                            odoo_id=p["id"], name=p["name"],
                            default_code=p.get("default_code") or None,
                            description=p.get("description") or None,
                            last_refreshed=now,
                        ))

                # Refresh vendors
                vendors = await client.search_read(
                    "res.partner", [["supplier_rank", ">", 0]],
                    ["name", "email"],
                    limit=5000,
                )

                existing_vendors_result = await db.execute(select(VendorCache))
                vendor_cache_map = {vc.odoo_id: vc for vc in existing_vendors_result.scalars().all()}

                for v in vendors:
                    email_domain = v.get("email", "").split("@")[-1] if v.get("email") and "@" in v["email"] else None
                    cached = vendor_cache_map.get(v["id"])
                    if cached:
                        cached.name = v["name"]
                        cached.email = v.get("email")
                        cached.email_domain = email_domain
                        cached.last_refreshed = now
                    else:
                        db.add(VendorCache(
                            odoo_id=v["id"], name=v["name"],
                            email=v.get("email"), email_domain=email_domain,
                            last_refreshed=now,
                        ))

                await client.close()

            except OdooSessionExpired:
                logger.warning(f"Odoo session expired for user {session.odoo_uid}")
            except Exception as e:
                logger.error(f"Cache refresh error for user {session.odoo_uid}: {e}")

        await db.commit()
        logger.info("Cache refresh complete")
