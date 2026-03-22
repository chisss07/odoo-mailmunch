import pytest
from app.services.email_classifier import classify_email, should_ignore


def test_should_ignore_sender_exact():
    rules = [{"field": "sender", "match_type": "exact", "value": "noreply@mycompany.com"}]
    assert should_ignore(sender="noreply@mycompany.com", subject="Invoice", rules=rules) is True
    assert should_ignore(sender="vendor@acme.com", subject="Invoice", rules=rules) is False


def test_should_ignore_domain():
    rules = [{"field": "domain", "match_type": "exact", "value": "electric-company.com"}]
    assert should_ignore(sender="billing@electric-company.com", subject="Bill", rules=rules) is True


def test_should_ignore_subject_contains():
    rules = [{"field": "subject", "match_type": "contains", "value": "Invoice from MyCompany"}]
    assert should_ignore(sender="x@y.com", subject="Invoice from MyCompany #123", rules=rules) is True
    assert should_ignore(sender="x@y.com", subject="Order Confirmed", rules=rules) is False


def test_classify_purchase_order():
    result = classify_email(
        subject="Order Confirmation #PO-4521",
        body="Your order has been confirmed. Items: Widget A, Qty: 50",
        sender_domain="acmewidgets.com",
        known_vendor_domains=["acmewidgets.com"],
    )
    assert result == "purchase_order"


def test_classify_shipping_notice():
    result = classify_email(
        subject="Your package has shipped",
        body="Tracking number: 1Z999AA10123456784. Estimated delivery: March 30",
        sender_domain="acmewidgets.com",
        known_vendor_domains=["acmewidgets.com"],
    )
    assert result == "shipping_notice"


def test_classify_unknown():
    result = classify_email(
        subject="Meeting tomorrow",
        body="Let's sync up at 2pm",
        sender_domain="random.com",
        known_vendor_domains=["acmewidgets.com"],
    )
    assert result == "unclassified"
