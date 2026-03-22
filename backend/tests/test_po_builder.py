import pytest
from app.services.po_builder import build_odoo_po_values


def test_build_po_values():
    draft = {
        "vendor_odoo_id": 1,
        "line_items": [
            {"product_odoo_id": 10, "description": "Widget A", "quantity": 50, "unit_price": 5.00},
            {"product_odoo_id": 11, "description": "Widget B", "quantity": 20, "unit_price": 12.50},
        ],
    }
    result = build_odoo_po_values(draft)
    assert result["partner_id"] == 1
    assert len(result["order_line"]) == 2
    assert result["order_line"][0][0] == 0
    assert result["order_line"][0][2]["product_qty"] == 50
    assert result["order_line"][1][2]["price_unit"] == 12.50
