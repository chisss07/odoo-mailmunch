from rapidfuzz import fuzz


def match_vendor(
    sender: str,
    sender_domain: str,
    vendors: list[dict],
    sender_name: str | None = None,
) -> dict | None:
    # Tier 1: Exact domain match
    for vendor in vendors:
        if vendor.get("email_domain") and vendor["email_domain"].lower() == sender_domain.lower():
            return {"odoo_id": vendor["odoo_id"], "name": vendor["name"], "confidence": "high"}

    # Tier 2: Fuzzy name match
    best_match = None
    best_score = 0
    name_to_match = sender_name or _extract_name_from_sender(sender)

    if name_to_match:
        for vendor in vendors:
            vendor_name = vendor.get("name", "")
            if not vendor_name:
                continue
            score = fuzz.token_sort_ratio(name_to_match.lower(), vendor_name.lower())
            if score > best_score and score >= 70:
                best_score = score
                best_match = vendor

    if best_match:
        confidence = "high" if best_score >= 90 else "medium" if best_score >= 80 else "low"
        return {"odoo_id": best_match["odoo_id"], "name": best_match["name"], "confidence": confidence}

    return None


def _extract_name_from_sender(sender: str) -> str | None:
    # "John Smith <john@example.com>" -> "John Smith"
    if "<" in sender:
        name = sender.split("<")[0].strip().strip('"')
        return name if name else None
    return None
