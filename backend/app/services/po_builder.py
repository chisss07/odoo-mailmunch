from app.services.odoo_client import OdooClient


def build_odoo_po_values(draft: dict, partner_id: int) -> dict:
    """Build Odoo purchase.order create values from a draft."""
    order_lines = []
    so_names = set()
    for item in draft["line_items"]:
        line_vals = {
            "product_qty": item["quantity"],
            "price_unit": item["unit_price"],
        }
        if item.get("product_odoo_id"):
            # Use the matched Odoo product and its name
            # (XML-RPC create doesn't trigger onchange, so we must set name explicitly)
            line_vals["product_id"] = item["product_odoo_id"]
            line_vals["name"] = item.get("product_name") or item.get("description", "")
        else:
            # No product match — use the email description as a free-text line
            line_vals["name"] = item.get("description", "")
        if item.get("sale_order_id"):
            line_vals["sale_order_id"] = item["sale_order_id"]
        if item.get("sales_order_name"):
            so_names.add(item["sales_order_name"])
        order_lines.append((0, 0, line_vals))

    values = {
        "partner_id": partner_id,
        "order_line": order_lines,
    }
    if so_names:
        values["origin"] = ", ".join(sorted(so_names))
    return values


async def _resolve_vendor(client: OdooClient, draft: dict) -> int:
    """Resolve or create the vendor partner_id in Odoo."""
    if draft.get("vendor_odoo_id"):
        return draft["vendor_odoo_id"]

    # Try to find by name
    vendor_name = draft.get("vendor_name", "Unknown Vendor")
    partners = await client.search_read(
        "res.partner",
        [["name", "ilike", vendor_name], ["supplier_rank", ">", 0]],
        ["id", "name"],
        limit=1,
    )
    if partners:
        return partners[0]["id"]

    # Create new vendor
    partner_id = await client.create("res.partner", {
        "name": vendor_name,
        "supplier_rank": 1,
    })
    return partner_id


async def create_po_in_odoo(client: OdooClient, draft: dict) -> dict:
    partner_id = await _resolve_vendor(client, draft)
    values = build_odoo_po_values(draft, partner_id)
    po_id = await client.create("purchase.order", values)
    pos = await client.search_read("purchase.order", [["id", "=", po_id]], ["name"])
    po_name = pos[0]["name"] if pos else f"PO-{po_id}"
    await client.call("purchase.order", "button_confirm", [[po_id]])
    return {"id": po_id, "name": po_name}


async def create_receipt_in_odoo(client: OdooClient, po_id: int, lines: list[dict] | None = None) -> dict:
    pickings = await client.search_read(
        "stock.picking",
        [["purchase_id", "=", po_id], ["state", "!=", "done"]],
        ["id", "name", "move_ids"],
    )

    if not pickings:
        raise ValueError(f"No pending receipt found for PO {po_id}")

    picking = pickings[0]

    if lines:
        for line in lines:
            await client.write("stock.move", [line["move_id"]], {"quantity": line["quantity"]})

    await client.call("stock.picking", "button_validate", [[picking["id"]]])
    return {"picking_id": picking["id"], "picking_name": picking["name"]}
