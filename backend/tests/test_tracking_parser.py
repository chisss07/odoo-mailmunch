import pytest
from app.services.tracking_parser import parse_tracking_info


def test_parse_ups_tracking():
    text = "Your package has shipped! UPS tracking number: 1Z999AA10123456784"
    result = parse_tracking_info(text)
    assert len(result["tracking_numbers"]) == 1
    assert result["tracking_numbers"][0]["number"] == "1Z999AA10123456784"
    assert result["tracking_numbers"][0]["carrier"] == "UPS"
    assert "ups.com" in result["tracking_numbers"][0]["url"]


def test_parse_fedex_tracking():
    text = "FedEx tracking: 961234567890"
    result = parse_tracking_info(text)
    assert result["tracking_numbers"][0]["carrier"] == "FedEx"


def test_parse_multiple_tracking():
    text = """
    Shipment 1: UPS 1Z999AA10123456784
    Shipment 2: FedEx 961234567890
    """
    result = parse_tracking_info(text)
    assert len(result["tracking_numbers"]) == 2


def test_fedex_not_matched_without_context():
    # A 13-digit invoice number should NOT be detected as FedEx without context
    text = "Invoice amount: $5,234.50. Order #9612345678901 submitted."
    result = parse_tracking_info(text)
    # Should not return this as a FedEx number
    fedex_numbers = [t for t in result["tracking_numbers"] if t["carrier"] == "FedEx"]
    assert len(fedex_numbers) == 0


def test_no_tracking_found():
    text = "Your order is confirmed. No shipment yet."
    result = parse_tracking_info(text)
    assert result["tracking_numbers"] == []
