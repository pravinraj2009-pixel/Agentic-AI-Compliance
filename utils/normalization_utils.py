from datetime import datetime


def normalize_invoice(raw):
    """
    Normalizes any parsed invoice into a strict, schema-safe format.

    INPUT:
        raw: dict (parser output)

    OUTPUT:
        dict with guaranteed structure
    """

    if not isinstance(raw, dict):
        raise TypeError(
            f"normalize_invoice expects dict, got {type(raw)}"
        )

    # ---------------------------------------------------------
    # Step 1: Extract fields safely
    # ---------------------------------------------------------

    fields = raw.get("fields")

    # Some parsers emit fields as list → convert
    if isinstance(fields, list):
        merged = {}
        for entry in fields:
            if isinstance(entry, dict):
                merged.update(entry)
        fields = merged

    if fields is None:
        fields = {}

    if not isinstance(fields, dict):
        raise TypeError("fields must be dict after normalization")

    # ---------------------------------------------------------
    # Step 2: Normalize top-level attributes
    # ---------------------------------------------------------

    invoice_id = (
        fields.get("invoice_number")
        or fields.get("invoice_id")
        or raw.get("invoice_id")
        or raw.get("id")
    )

    invoice_date = (
        fields.get("invoice_date")
        or raw.get("invoice_date")
    )

    # ---- Handle nested vendor/buyer structures ----
    vendor = fields.get("vendor") or raw.get("vendor") or {}
    buyer = fields.get("buyer") or raw.get("buyer") or {}
    
    seller_gstin = (
        fields.get("seller_gstin")
        or raw.get("seller_gstin")
        or (vendor.get("gstin") if isinstance(vendor, dict) else None)
    )

    buyer_gstin = (
        fields.get("buyer_gstin")
        or raw.get("buyer_gstin")
        or (buyer.get("gstin") if isinstance(buyer, dict) else None)
    )

    invoice_value = (
        fields.get("invoice_value")
        or raw.get("invoice_value")
        or fields.get("total_amount")
        or raw.get("total_amount")
        or 0
    )

    # ---------------------------------------------------------
    # Step 3: Normalize line items
    # ---------------------------------------------------------

    raw_items = (
        raw.get("line_items")
        or fields.get("line_items")
        or []
    )

    if not isinstance(raw_items, list):
        raw_items = []

    line_items = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        line_items.append({
            "description": item.get("description"),
            "quantity": _safe_float(item.get("quantity")),
            "rate": _safe_float(item.get("rate")),
            "amount": _safe_float(item.get("amount")),
            "hsn_code": item.get("hsn_code"),
            "igst_rate": _safe_float(item.get("igst_rate")),
            "cgst_rate": _safe_float(item.get("cgst_rate")),
            "sgst_rate": _safe_float(item.get("sgst_rate")),
        })

    # ---------------------------------------------------------
    # Step 4: Assemble normalized invoice
    # ---------------------------------------------------------

    normalized = {
        "invoice_id": str(invoice_id) if invoice_id else None,
        "invoice_date": _normalize_date(invoice_date),
        "seller_gstin": seller_gstin,
        "buyer_gstin": buyer_gstin,
        "invoice_value": _safe_float(invoice_value),
        "line_items": line_items,
        "fields": fields,
    }

    return normalized


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None
