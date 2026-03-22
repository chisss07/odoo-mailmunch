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
    text = "FedEx tracking: 794644790138"
    result = parse_tracking_info(text)
    assert result["tracking_numbers"][0]["carrier"] == "FedEx"


def test_parse_multiple_tracking():
    text = """
    Shipment 1: UPS 1Z999AA10123456784
    Shipment 2: FedEx 794644790138
    """
    result = parse_tracking_info(text)
    assert len(result["tracking_numbers"]) == 2


def test_no_tracking_found():
    text = "Your order is confirmed. No shipment yet."
    result = parse_tracking_info(text)
    assert result["tracking_numbers"] == []
