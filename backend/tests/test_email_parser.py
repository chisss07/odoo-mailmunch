import pytest
from app.services.email_parser import parse_order_details


def test_parse_structured_order():
    text = """
    Order Confirmation #PO-4521

    Vendor: Acme Widgets
    Date: March 25, 2026

    Items:
    1. Widget A (SKU: WA-100) - Qty: 50 - $5.00 each
    2. Widget B (SKU: WB-200) - Qty: 20 - $12.50 each

    Subtotal: $500.00
    Total: $500.00
    """
    result = parse_order_details(text)
    assert result["order_number"] == "PO-4521"
    assert len(result["line_items"]) == 2
    assert result["line_items"][0]["sku"] == "WA-100"
    assert result["line_items"][0]["quantity"] == 50
    assert result["line_items"][0]["unit_price"] == 5.00


def test_parse_informal_order():
    text = """
    Hi Paul,

    Your order for 50 widgets at $5 each has been confirmed.
    Order number: 12345
    Expected delivery: March 30, 2026
    """
    result = parse_order_details(text)
    assert result["order_number"] == "12345"
    assert len(result["line_items"]) >= 1


def test_parse_empty_text():
    result = parse_order_details("")
    assert result["line_items"] == []
    assert result["order_number"] is None
