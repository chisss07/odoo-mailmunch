import re
from dataclasses import dataclass, field


@dataclass
class LineItem:
    description: str = ""
    sku: str | None = None
    quantity: float = 0
    unit_price: float = 0
    confidence: str = "low"  # high/medium/low


@dataclass
class ParsedOrder:
    order_number: str | None = None
    vendor_name: str | None = None
    line_items: list[dict] = field(default_factory=list)
    total_amount: float | None = None
    expected_date: str | None = None
    raw_text: str = ""


# Patterns for order numbers
ORDER_PATTERNS = [
    r"(?:order|PO|purchase\s*order|confirmation)\s*#?\s*:?\s*([A-Za-z0-9\-]+\d+)",
    r"#\s*([A-Za-z]*\-?\d{4,})",
    r"(?:order|PO)\s+number\s*:?\s*(\d+)",
]

# Patterns for line items with SKU, qty, price
LINE_ITEM_PATTERNS = [
    # "Widget A (SKU: WA-100) - Qty: 50 - $5.00 each"
    r"(.+?)\s*\((?:SKU|sku|Sku)\s*:\s*([A-Za-z0-9\-]+)\)\s*[-–]\s*(?:Qty|qty|Quantity)\s*:\s*(\d+)\s*[-–]\s*\$?([\d,.]+)",
    # "50 x Widget A @ $5.00"
    r"(\d+)\s*[xX×]\s*(.+?)\s*[@aAtT]\s*\$?([\d,.]+)",
    # "Widget A - 50 - $5.00"
    r"(.+?)\s*[-–]\s*(\d+)\s*[-–]\s*\$?([\d,.]+)",
]

# Pattern for informal "N items at $X each"
INFORMAL_PATTERN = r"(\d+)\s+(\w[\w\s]*?)\s+(?:at|@)\s+\$?([\d,.]+)\s*(?:each|ea|per)?"

# Date patterns
DATE_PATTERNS = [
    r"(?:deliver|ship|arrival|expected|ETA)\s*(?:date)?\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
    r"(?:deliver|ship)\s+(?:by|on)\s+(\w+\s+\d{1,2},?\s+\d{4})",
]

# Total patterns
TOTAL_PATTERNS = [
    r"(?:total|amount)\s*:?\s*\$?([\d,.]+)",
    r"\$\s*([\d,.]+)\s*(?:total|due)",
]


def parse_order_details(text: str) -> dict:
    if not text.strip():
        return {"order_number": None, "vendor_name": None, "line_items": [], "total_amount": None, "expected_date": None}

    order_number = _extract_first_match(text, ORDER_PATTERNS)
    line_items = _extract_line_items(text)
    total_amount = _extract_total(text)
    expected_date = _extract_first_match(text, DATE_PATTERNS)

    return {
        "order_number": order_number,
        "vendor_name": None,  # Resolved by vendor_matcher later
        "line_items": [_line_item_to_dict(li) for li in line_items],
        "total_amount": total_amount,
        "expected_date": expected_date,
    }


def _extract_first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_line_items(text: str) -> list[LineItem]:
    items = []

    # Try structured patterns; stop after the first pattern that yields results
    for pattern in LINE_ITEM_PATTERNS:
        pattern_items = []
        for match in re.finditer(pattern, text):
            groups = match.groups()
            if len(groups) == 4:
                # SKU pattern: description, sku, qty, price
                pattern_items.append(LineItem(
                    description=groups[0].strip(),
                    sku=groups[1].strip(),
                    quantity=float(groups[2].replace(",", "")),
                    unit_price=float(groups[3].replace(",", "")),
                    confidence="high",
                ))
            elif len(groups) == 3:
                # Check if first group is numeric (qty x desc @ price)
                if groups[0].replace(",", "").isdigit():
                    pattern_items.append(LineItem(
                        description=groups[1].strip(),
                        quantity=float(groups[0].replace(",", "")),
                        unit_price=float(groups[2].replace(",", "")),
                        confidence="medium",
                    ))
                else:
                    pattern_items.append(LineItem(
                        description=groups[0].strip(),
                        quantity=float(groups[1].replace(",", "")),
                        unit_price=float(groups[2].replace(",", "")),
                        confidence="medium",
                    ))
        if pattern_items:
            items = pattern_items
            break

    # Try informal pattern if nothing found
    if not items:
        for match in re.finditer(INFORMAL_PATTERN, text, re.IGNORECASE):
            items.append(LineItem(
                description=match.group(2).strip(),
                quantity=float(match.group(1).replace(",", "")),
                unit_price=float(match.group(3).replace(",", "")),
                confidence="low",
            ))

    return items


def _extract_total(text: str) -> float | None:
    for pattern in TOTAL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def _line_item_to_dict(item: LineItem) -> dict:
    return {
        "description": item.description,
        "sku": item.sku,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "confidence": item.confidence,
    }
