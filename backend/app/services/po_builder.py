from app.services.odoo_client import OdooClient


def build_odoo_po_values(draft: dict) -> dict:
    """Build Odoo purchase.order create values from a draft."""
    order_lines = []
    for item in draft["line_items"]:
        line_vals = {
            "product_id": item.get("product_odoo_id"),
            "name": item.get("description", ""),
            "product_qty": item["quantity"],
            "price_unit": item["unit_price"],
        }
        order_lines.append((0, 0, line_vals))

    return {
        "partner_id": draft["vendor_odoo_id"],
        "order_line": order_lines,
    }


async def create_po_in_odoo(client: OdooClient, draft: dict) -> dict:
    values = build_odoo_po_values(draft)
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
