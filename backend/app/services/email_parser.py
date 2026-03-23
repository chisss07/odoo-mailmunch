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
    r"(?:Invoice\s*No\.?|order|PO|purchase\s*order|confirmation)\s*#?\s*:?\s*([A-Za-z0-9\-]+\d+)",
    r"(?:Order\s+Number|PO\s+Number)\s*:?\s*([A-Za-z0-9\-]+\d+)",
    r"Order\s*#\s*\n\s*(\d[\d\-]+\d)",  # Amazon: "Order #\n113-1207070-0461035"
    r"#\s*([A-Za-z]*\-?\d{4,})",
    r"(?:order|PO)\s+number\s*:?\s*(\d+)",
]

# Patterns for line items with SKU, qty, price
LINE_ITEM_PATTERNS = [
    # "Widget A (SKU: WA-100) - Qty: 50 - $5.00 each"
    r"(.+?)\s*\((?:SKU|sku|Sku)\s*:\s*([A-Za-z0-9\-]+)\)\s*[-–]\s*(?:Qty|qty|Quantity)\s*:\s*(\d+)\s*[-–]\s*\$?([\d,.]+)",
    # "50 x Widget A @ $5.00"
    r"(\d+)\s*[xX×]\s*(.+?)\s*[@aAtT]\s*\$?([\d,.]+)",
    # "Widget A - 50 - $5.00" (description must start with a letter, not a digit)
    r"([A-Za-z].+?)\s*[-–]\s*(\d+)\s*[-–]\s*\$?([\d,.]+)",
]

# Pattern for informal "N items at $X each"
INFORMAL_PATTERN = r"(\d+)\s+(\w[\w\s]{1,50}?)\s+(?:at|@)\s+\$?([\d,.]+)\s*(?:each|ea|per)?"

# Date patterns
DATE_PATTERNS = [
    r"(?:deliver|ship|arrival|expected|ETA)\s*(?:date)?\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
    r"(?:deliver|ship)\s+(?:by|on)\s+(\w+\s+\d{1,2},?\s+\d{4})",
    r"(?:Invoice\s*Date)\s*:?\s*(\d{4}/\d{2}/\d{2})",
]

# Total patterns
TOTAL_PATTERNS = [
    r"^Total\s+\$?([\d,.]+)\s*$",  # "Total $322.60" on its own line
    r"Grand\s+Total\s*:?\s*\n?\s*([\d,.]+)\s*USD",  # Amazon: "Grand Total:\n733.7 USD"
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
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
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
            try:
                if len(groups) == 4:
                    pattern_items.append(LineItem(
                        description=groups[0].strip(),
                        sku=groups[1].strip(),
                        quantity=float(groups[2].replace(",", "")),
                        unit_price=float(groups[3].replace(",", "")),
                        confidence="high",
                    ))
                elif len(groups) == 3:
                    if groups[0].replace(",", "").isdigit():
                        qty_val = float(groups[0].replace(",", ""))
                        price_val = float(groups[2].replace(",", ""))
                        if qty_val > 50000 or price_val > 500000:
                            continue
                        pattern_items.append(LineItem(
                            description=groups[1].strip(),
                            quantity=qty_val,
                            unit_price=price_val,
                            confidence="medium",
                        ))
                    else:
                        qty_val = float(groups[1].replace(",", ""))
                        price_val = float(groups[2].replace(",", ""))
                        if qty_val > 50000 or price_val > 500000:
                            continue
                        pattern_items.append(LineItem(
                            description=groups[0].strip(),
                            quantity=qty_val,
                            unit_price=price_val,
                            confidence="medium",
                        ))
            except (ValueError, IndexError):
                continue
        if pattern_items:
            items = pattern_items
            break

    # Try tabular invoice format (PDF-extracted multi-line blocks)
    if not items:
        items = _extract_tabular_items(text)

    # Try SKU/unit/each block pattern (from HTML-to-text conversion)
    if not items:
        items = _extract_sku_block_items(text)

    # Try Amazon-style "* item\n  Quantity: N\n  XX.XX USD" pattern
    if not items:
        items = _extract_amazon_items(text)

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


def _extract_tabular_items(text: str) -> list[LineItem]:
    """Parse tabular invoice formats where PDF extraction puts each column on its own line.

    Handles the Ubiquiti-style format:
        1                          ← line number
        Access Fail-Secure ...     ← description
        UACC-Lock-Strike-...      ← SKU
        Tariff Surcharge Fee       ← fee line (optional)
        830140 1                   ← HS code + qty
        1                          ← fee qty (optional)
        $89.00                     ← unit price
        $6.41                      ← fee price (optional)
        ...more prices...
    """
    lines = text.splitlines()
    items = []

    # Detect if this is a tabular invoice by looking for the header
    header_idx = None
    for i, line in enumerate(lines):
        if re.search(r"NO\.\s+PRODUCT\s+DESCRIPTION", line, re.IGNORECASE):
            header_idx = i
            break
        if re.search(r"DESCRIPTION\s+.*QTY\s+.*PRICE", line, re.IGNORECASE):
            header_idx = i
            break

    if header_idx is None:
        return []

    # Find the end of line items (Total/Shipping/Tax summary lines)
    end_idx = len(lines)
    for i in range(header_idx + 1, len(lines)):
        if re.match(r"^\s*(Total\s+Amount|Shipping\s+Amount|Tariff\s+Amount|Subtotal|Tax)", lines[i], re.IGNORECASE):
            end_idx = i
            break

    # Parse the block between header and totals
    block_lines = lines[header_idx + 1 : end_idx]

    # Strategy: find line-number anchors (a line that is just a digit like "1", "2", "3")
    # Each anchor starts a new item block. Line numbers are sequential.
    item_blocks = []
    current_block = []
    expected_line_no = 1

    for line in block_lines:
        stripped = line.strip()
        if not stripped:
            continue
        # A standalone number matching the expected sequence signals a new item
        if re.match(r"^\d{1,2}$", stripped) and int(stripped) == expected_line_no:
            if current_block:
                item_blocks.append(current_block)
            current_block = [stripped]
            expected_line_no += 1
        else:
            current_block.append(stripped)

    if current_block:
        item_blocks.append(current_block)

    # Parse each block
    for block in item_blocks:
        if len(block) < 3:
            continue

        line_no = block[0]  # "1", "2", etc.

        # Collect text lines (descriptions, SKUs) and price lines ($X.XX)
        text_lines = []
        prices = []
        hs_qty_line = None

        for entry in block[1:]:
            price_match = re.match(r"^\$([\d,.]+)$", entry)
            hs_qty_match = re.match(r"^(\d{4,})\s+(\d+)$", entry)

            if price_match:
                prices.append(float(price_match.group(1).replace(",", "")))
            elif hs_qty_match:
                hs_qty_line = hs_qty_match
            else:
                text_lines.append(entry)

        if not text_lines or not prices:
            continue

        # First text line is the description, second is often the SKU
        description = text_lines[0]
        sku = None
        fee_description = None

        for tl in text_lines[1:]:
            # SKU-like: contains hyphens and alphanumeric, no spaces (or very few)
            if re.match(r"^[A-Za-z0-9][\w\-]+$", tl) and "-" in tl:
                sku = tl
            elif re.search(r"(?:fee|surcharge|tariff)", tl, re.IGNORECASE):
                fee_description = tl

        # Extract quantity from HS code line
        qty = 1.0
        if hs_qty_line:
            qty = float(hs_qty_line.group(2))

        # First price is the main item unit price
        unit_price = prices[0] if prices else 0.0

        items.append(LineItem(
            description=description,
            sku=sku,
            quantity=qty,
            unit_price=unit_price,
            confidence="high",
        ))

        # If there's a fee line with its own price, add it as a separate item
        if fee_description and len(prices) >= 2:
            items.append(LineItem(
                description=fee_description,
                quantity=1,
                unit_price=prices[1],
                confidence="medium",
            ))

    return items


def _extract_total(text: str) -> float | None:
    # For tabular invoices, prefer the last standalone "Total $X" (the grand total)
    # Check for a clear "Total $X" at end first
    grand_total = re.search(r"^Total\s+\$?([\d,.]+)\s*$", text, re.IGNORECASE | re.MULTILINE)
    if grand_total:
        return float(grand_total.group(1).replace(",", ""))

    for pattern in TOTAL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def parse_html_order_details(html: str) -> dict:
    """Parse order details directly from HTML email content.

    Extracts structured data from HTML patterns like:
      - SKU in URL params (?sku=XXX) or text "SKU: XXX"
      - Quantity from "N unit(s)" text
      - Price from "$XXX.XX each" text
      - Product name from link text or alt attributes
    """
    if not html:
        return {"order_number": None, "vendor_name": None, "line_items": [], "total_amount": None, "expected_date": None}

    from app.services.text_extractor import html_to_text
    plain = html_to_text(html)

    # Get order number and total from plain text
    order_number = _extract_first_match(plain, ORDER_PATTERNS)
    total_amount = _extract_total(plain)
    expected_date = _extract_first_match(plain, DATE_PATTERNS)

    # Extract items from HTML structure
    items = _extract_html_line_items(html)

    return {
        "order_number": order_number,
        "vendor_name": None,
        "line_items": [_line_item_to_dict(li) for li in items],
        "total_amount": total_amount,
        "expected_date": expected_date,
    }


def _extract_html_line_items(html: str) -> list[LineItem]:
    """Extract line items from HTML email by finding SKU/qty/price patterns."""
    items = []

    # Find all SKU mentions with surrounding context
    # Pattern: find blocks that contain "SKU: XXX" text
    sku_pattern = re.compile(
        r"SKU:\s*([A-Za-z0-9][\w\-]*)",
        re.IGNORECASE,
    )

    # Find "$X.XX each" prices
    each_price_pattern = re.compile(r"\$([\d,.]+)\s*each", re.IGNORECASE)

    # Find "N unit(s)" quantities
    unit_qty_pattern = re.compile(r"(\d+)\s*units?", re.IGNORECASE)

    # Find product names in link text (anchor tags with product descriptions)
    # These are typically in <a> tags with product URLs
    product_link_pattern = re.compile(
        r'<a[^>]*href=["\'][^"\']*product[^"\']*\?sku[^"\']*["\'][^>]*>'
        r'\s*(.*?)\s*</a>',
        re.IGNORECASE | re.DOTALL,
    )

    # Strategy: split HTML into item blocks and extract from each
    # Look for repeating table structures separated by borders
    # Each item block typically contains: product link, SKU div, qty div, price cells

    # Find all product links with SKU in URL
    product_links = list(product_link_pattern.finditer(html))

    if not product_links:
        # Try alt attributes from img tags as fallback
        alt_pattern = re.compile(
            r'<a[^>]*href=["\'][^"\']*product[^"\']*["\'][^>]*>.*?'
            r'<img[^>]*alt=["\']([^"\']+)["\']',
            re.IGNORECASE | re.DOTALL,
        )
        product_links = list(alt_pattern.finditer(html))

    if not product_links:
        return []

    # For each product link, find the surrounding block and extract SKU, qty, price
    seen_descriptions = set()
    for link_match in product_links:
        # Get product description from link text, strip HTML tags
        desc_raw = link_match.group(1)
        description = re.sub(r"<[^>]+>", "", desc_raw).strip()
        description = re.sub(r"\s+", " ", description)

        if not description or len(description) < 3:
            continue

        # Skip duplicate descriptions (same product link appears twice: image + text)
        if description in seen_descriptions:
            continue
        seen_descriptions.add(description)

        # Search in a window after this match for SKU, qty, price
        window_start = link_match.start()
        window_end = min(len(html), link_match.end() + 2000)
        window = html[window_start:window_end]

        # Extract SKU
        sku_match = sku_pattern.search(window)
        sku = sku_match.group(1) if sku_match else None

        # Also try SKU from URL param
        if not sku:
            url_sku = re.search(r'[?&]sku=([A-Za-z0-9][\w\-]*)', window, re.IGNORECASE)
            if url_sku:
                sku = url_sku.group(1)

        # Extract quantity
        qty_match = unit_qty_pattern.search(window)
        quantity = float(qty_match.group(1)) if qty_match else 1.0

        # Extract price ("$X.XX each")
        price_match = each_price_pattern.search(window)
        unit_price = float(price_match.group(1).replace(",", "")) if price_match else 0.0

        items.append(LineItem(
            description=description,
            sku=sku,
            quantity=quantity,
            unit_price=unit_price,
            confidence="high" if sku and unit_price > 0 else "medium",
        ))

    return items


def _extract_sku_block_items(text: str) -> list[LineItem]:
    """Parse items from text with SKU/unit/each patterns (from HTML-to-text conversion).

    Handles patterns like:
        Product Name
        SKU: U7-Pro-Max
        Brand: Ubiquiti
        1 unit
        $263.75 each
        $263.75
    """
    items = []
    lines = text.splitlines()

    for i, line in enumerate(lines):
        sku_match = re.match(r"^\s*SKU:\s*([A-Za-z0-9][\w\-]*)", line, re.IGNORECASE)
        if not sku_match:
            continue

        sku = sku_match.group(1)

        # Look backwards for description (first non-empty, non-SKU, non-Brand line)
        description = sku
        for j in range(i - 1, max(i - 5, -1), -1):
            prev = lines[j].strip()
            if not prev:
                continue
            if re.match(r"^(SKU|Brand|Sign In)\s*:", prev, re.IGNORECASE):
                continue
            if len(prev) > 5:
                description = prev
                break

        # Look forward for quantity and price
        quantity = 1.0
        unit_price = 0.0
        for j in range(i + 1, min(i + 8, len(lines))):
            fwd = lines[j].strip()
            qty_match = re.match(r"^(\d+)\s+units?$", fwd, re.IGNORECASE)
            price_match = re.match(r"^\$([\d,.]+)\s+each$", fwd, re.IGNORECASE)
            if qty_match:
                quantity = float(qty_match.group(1))
            if price_match:
                unit_price = float(price_match.group(1).replace(",", ""))

        items.append(LineItem(
            description=description,
            sku=sku,
            quantity=quantity,
            unit_price=unit_price,
            confidence="high" if unit_price > 0 else "medium",
        ))

    return items


def _extract_amazon_items(text: str) -> list[LineItem]:
    """Parse Amazon-style order confirmations.

    Format:
        * Product Description Here
          Quantity: 2
          99.99 USD
    """
    items = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for lines starting with "* " (bullet item)
        if line.startswith("* "):
            description = line[2:].strip()
            quantity = 1.0
            unit_price = 0.0

            # Look ahead for Quantity and price (stop at blank lines or next bullet)
            for j in range(i + 1, min(i + 6, len(lines))):
                fwd = lines[j].strip()
                if not fwd or fwd.startswith("* "):
                    break
                qty_match = re.match(r"Quantity:\s*(\d+)", fwd, re.IGNORECASE)
                price_match = re.match(r"([\d,.]+)\s*USD", fwd, re.IGNORECASE)
                if qty_match:
                    quantity = float(qty_match.group(1))
                if price_match:
                    unit_price = float(price_match.group(1).replace(",", ""))

            if unit_price > 0:
                items.append(LineItem(
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    confidence="high",
                ))
        i += 1

    return items


def _line_item_to_dict(item: LineItem) -> dict:
    return {
        "description": item.description,
        "sku": item.sku,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "confidence": item.confidence,
    }
