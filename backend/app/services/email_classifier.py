import re


def should_ignore(sender: str, subject: str, rules: list[dict]) -> bool:
    for rule in rules:
        field_value = ""
        if rule["field"] == "sender":
            field_value = sender
        elif rule["field"] == "domain":
            field_value = sender.split("@")[-1].lower() if "@" in sender else ""
        elif rule["field"] == "subject":
            field_value = subject

        if rule["match_type"] == "exact":
            if field_value.lower() == rule["value"].lower():
                return True
        elif rule["match_type"] == "contains":
            if rule["value"].lower() in field_value.lower():
                return True
        elif rule["match_type"] == "regex":
            try:
                if re.search(rule["value"], field_value, re.IGNORECASE):
                    return True
            except re.error:
                pass  # Malformed regex — treat as non-match

    return False


# Keywords for classification
PO_KEYWORDS = [
    r"order\s+confirm",
    r"purchase\s+order",
    r"\bPO[\s\-#]",
    r"order\s+#",
    r"order\s+has\s+been\s+(?:confirmed|placed|received)",
    r"invoice\s+(?:for|from)\s+(?:your\s+)?order",
    r"\bquot(?:e|ation)\s+accepted",
]

SHIPPING_KEYWORDS = [
    r"has\s+shipped",
    r"shipment\s+(?:notice|notification|update)",
    r"tracking\s+(?:number|info|#)",
    r"out\s+for\s+delivery",
    r"package\s+(?:shipped|dispatched|sent)",
    r"delivery\s+(?:notice|confirmation)",
    r"\b(?:UPS|FedEx|USPS|DHL)\b.*\btrack",
]

BILL_KEYWORDS = [
    r"(?:payment|amount)\s+due",
    r"please\s+(?:pay|remit)",
    r"bill\s+(?:for|from)",
    r"statement\s+of\s+account",
]


def classify_email(
    subject: str,
    body: str,
    sender_domain: str,
    known_vendor_domains: list[str],
) -> str:
    MAX_CLASSIFY_CHARS = 50_000
    combined = f"{subject} {body}"[:MAX_CLASSIFY_CHARS]

    is_known_vendor = sender_domain.lower() in [d.lower() for d in known_vendor_domains]

    # Check shipping first (more specific)
    shipping_score = _keyword_score(combined, SHIPPING_KEYWORDS)
    if shipping_score >= 1:
        return "shipping_notice"

    # Check PO
    po_score = _keyword_score(combined, PO_KEYWORDS)
    if po_score >= 1:
        return "purchase_order"

    # Check bill
    bill_score = _keyword_score(combined, BILL_KEYWORDS)
    if bill_score >= 1:
        return "bill"

    # If from known vendor but unclear, assume purchase_order
    if is_known_vendor and _has_order_indicators(combined):
        return "purchase_order"

    return "unclassified"


def _keyword_score(text: str, patterns: list[str]) -> float:
    score = 0
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 1
    return score


def _has_order_indicators(text: str) -> bool:
    """Check for generic order indicators like prices, quantities, item lists."""
    has_price = bool(re.search(r"\$\d+", text))
    has_quantity = bool(re.search(r"(?:qty|quantity|x\s*\d|\d\s*x)", text, re.IGNORECASE))
    return has_price and has_quantity
