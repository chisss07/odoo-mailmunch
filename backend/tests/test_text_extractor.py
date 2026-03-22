import pytest
from app.services.text_extractor import html_to_text, extract_text_from_eml


def test_html_to_text_strips_tags():
    html = "<html><body><p>Hello <b>World</b></p><br><p>Line 2</p></body></html>"
    result = html_to_text(html)
    assert "Hello World" in result
    assert "Line 2" in result
    assert "<" not in result


def test_html_to_text_empty():
    assert html_to_text("") == ""
    assert html_to_text(None) == ""


def test_html_to_text_ignores_style_content():
    html = "<html><head><style>body { color: red; font-size: 14px; }</style></head><body><p>Hello</p></body></html>"
    result = html_to_text(html)
    assert "color" not in result
    assert "font-size" not in result
    assert "Hello" in result


def test_extract_text_from_eml_plain():
    eml_content = (
        "From: vendor@acme.com\r\n"
        "Subject: Order Confirmed\r\n"
        "Content-Type: text/plain\r\n"
        "\r\n"
        "Your order #123 is confirmed.\n"
        "Item: Widget A, Qty: 10, Price: $5.00\n"
    )
    result = extract_text_from_eml(eml_content.encode())
    assert "Order Confirmed" in result["subject"]
    assert "vendor@acme.com" in result["sender"]
    assert "Widget A" in result["body"]
