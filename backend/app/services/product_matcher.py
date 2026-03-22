from rapidfuzz import fuzz, process


def match_product(
    description: str,
    sku: str | None,
    products: list[dict],
    vendor_products: list[dict] | None = None,
    top_n: int = 3,
) -> dict | None:
    if not products:
        return None

    # Tier 1: Exact SKU match
    if sku:
        for product in products:
            if product.get("default_code") and product["default_code"].upper() == sku.upper():
                alternatives = _get_alternatives(description, products, exclude_id=product["odoo_id"], top_n=top_n)
                return {
                    "odoo_id": product["odoo_id"],
                    "name": product["name"],
                    "confidence": "high",
                    "alternatives": alternatives,
                }

    # Tier 2: Vendor-product mapping
    if vendor_products:
        for vp in vendor_products:
            if vp.get("vendor_product_code") and sku and vp["vendor_product_code"].upper() == sku.upper():
                product = next((p for p in products if p["odoo_id"] == vp["product_odoo_id"]), None)
                if product:
                    alternatives = _get_alternatives(description, products, exclude_id=product["odoo_id"], top_n=top_n)
                    return {
                        "odoo_id": product["odoo_id"],
                        "name": product["name"],
                        "confidence": "high",
                        "alternatives": alternatives,
                    }

    # Tier 3: Fuzzy name match — token_set_ratio handles subset descriptions better
    product_names = {p["odoo_id"]: p["name"] for p in products}
    matches = process.extract(description, product_names, scorer=fuzz.token_set_ratio, limit=top_n + 1)

    if not matches:
        return None

    _, best_score, best_id = matches[0]
    if best_score < 50:
        return None

    best_product = next(p for p in products if p["odoo_id"] == best_id)
    confidence = "high" if best_score >= 90 else "medium" if best_score >= 70 else "low"

    alternatives = [
        {"odoo_id": pid, "name": name, "score": score}
        for name, score, pid in matches[1:]
        if score >= 40
    ]

    return {
        "odoo_id": best_product["odoo_id"],
        "name": best_product["name"],
        "confidence": confidence,
        "alternatives": alternatives,
    }


def _get_alternatives(description: str, products: list[dict], exclude_id: int, top_n: int) -> list[dict]:
    product_names = {p["odoo_id"]: p["name"] for p in products if p["odoo_id"] != exclude_id}
    if not product_names:
        return []
    matches = process.extract(description, product_names, scorer=fuzz.token_sort_ratio, limit=top_n)
    return [
        {"odoo_id": pid, "name": name, "score": score}
        for name, score, pid in matches
        if score >= 40
    ]
