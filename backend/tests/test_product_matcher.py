import pytest
from app.services.product_matcher import match_product


def test_match_by_sku_exact():
    products = [
        {"odoo_id": 10, "name": "Widget A", "default_code": "WA-100", "description": ""},
        {"odoo_id": 11, "name": "Widget B", "default_code": "WB-200", "description": ""},
    ]
    result = match_product(description="Widget A", sku="WA-100", products=products)
    assert result["odoo_id"] == 10
    assert result["confidence"] == "high"


def test_match_by_name_fuzzy():
    products = [
        {"odoo_id": 10, "name": "Stainless Steel Widget Type A", "default_code": None, "description": ""},
    ]
    result = match_product(description="Steel Widget A", sku=None, products=products)
    assert result["odoo_id"] == 10
    assert result["confidence"] in ("medium", "high")


def test_match_returns_alternatives():
    products = [
        {"odoo_id": 10, "name": "Widget A", "default_code": "WA-100", "description": ""},
        {"odoo_id": 11, "name": "Widget A Pro", "default_code": "WA-200", "description": ""},
        {"odoo_id": 12, "name": "Gadget B", "default_code": "GB-100", "description": ""},
    ]
    result = match_product(description="Widget A", sku=None, products=products)
    assert result["odoo_id"] == 10
    assert len(result["alternatives"]) >= 1


def test_no_match():
    products = [
        {"odoo_id": 10, "name": "Widget A", "default_code": "WA-100", "description": ""},
    ]
    result = match_product(description="Completely Different Item", sku="ZZZZZ", products=products)
    assert result is None or result["confidence"] == "low"
