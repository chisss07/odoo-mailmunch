import pytest
from app.services.vendor_matcher import match_vendor


def test_match_by_email_domain():
    vendors = [
        {"odoo_id": 1, "name": "Acme Widgets", "email_domain": "acmewidgets.com"},
        {"odoo_id": 2, "name": "FastBolts Inc", "email_domain": "fastbolts.com"},
    ]
    result = match_vendor(sender="orders@acmewidgets.com", sender_domain="acmewidgets.com", vendors=vendors)
    assert result["odoo_id"] == 1
    assert result["confidence"] == "high"


def test_match_by_name_fuzzy():
    vendors = [
        {"odoo_id": 1, "name": "Acme Widgets LLC", "email_domain": "acme.com"},
    ]
    result = match_vendor(sender="John <john@random.com>", sender_domain="random.com", vendors=vendors, sender_name="Acme Widgets")
    assert result["odoo_id"] == 1
    assert result["confidence"] == "medium"


def test_no_match():
    vendors = [
        {"odoo_id": 1, "name": "Acme Widgets", "email_domain": "acmewidgets.com"},
    ]
    result = match_vendor(sender="unknown@nowhere.com", sender_domain="nowhere.com", vendors=vendors)
    assert result is None
