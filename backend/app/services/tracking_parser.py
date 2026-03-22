import re

CARRIER_PATTERNS = {
    "UPS": {
        "pattern": r"1Z[A-Z0-9]{16}",
        "url_template": "https://www.ups.com/track?tracknum={number}",
    },
    "FedEx": {
        "pattern": r"\b((?:61|96|98|77|01|02)\d{10,11}|(?:7489|7491)\d{12})\b",
        "url_template": "https://www.fedex.com/fedextrack/?trknbr={number}",
        "context_required": True,
    },
    "USPS": {
        "pattern": r"\b(9[2-4]\d{20,22})\b",
        "url_template": "https://tools.usps.com/go/TrackConfirmAction?tLabels={number}",
    },
    "DHL": {
        "pattern": r"\b\d{10,11}\b",
        "url_template": "https://www.dhl.com/en/express/tracking.html?AWB={number}",
        "context_required": True,
    },
}

TRACKING_CONTEXT_PATTERN = r"(?:track(?:ing)?|ship(?:ment|ped)?|carrier|deliver)"


def parse_tracking_info(text: str) -> dict:
    tracking_numbers = []
    text_lower = text.lower()

    for carrier, config in CARRIER_PATTERNS.items():
        matches = re.finditer(config["pattern"], text)
        for match in matches:
            number = match.group(0)

            # For carriers that need context, check for carrier name or tracking keywords nearby
            if config.get("context_required"):
                # Check within 100 chars of the match
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text_lower[start:end]
                if carrier.lower() not in context and not re.search(TRACKING_CONTEXT_PATTERN, context):
                    continue

            tracking_numbers.append({
                "number": number,
                "carrier": carrier,
                "url": config["url_template"].format(number=number),
            })

    return {
        "tracking_numbers": tracking_numbers,
        "estimated_delivery": _extract_delivery_date(text),
    }


def _extract_delivery_date(text: str) -> str | None:
    patterns = [
        r"(?:estimated|expected)\s+delivery\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
        r"(?:deliver|arrive)\s+(?:by|on)\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"ETA\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
