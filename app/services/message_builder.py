"""
Build SMS body in the exact format:

Oda Namba <Order Number>
<Customer name>
<Customer phone>/<Alt Phone>
<Product Name>
<Price of Product>
<Address>, <City>
"""


def _get(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _ensure_leading_zero(s: str) -> str:
    """Ensure phone number in message text starts with 0 (Tanzanian local format)."""
    digits = "".join(c for c in s if c.isdigit())
    if not digits:
        return s
    if digits.startswith("0"):
        return digits  # Already has leading 0
    # E.164 255XXXXXXXXX → 0XXXXXXXXX
    if digits.startswith("255") and len(digits) == 12:
        return "0" + digits[3:]
    # 9-digit local (e.g. 748415123) → 0748415123
    if len(digits) == 9 and digits[0] == "7":
        return "0" + digits
    if digits[0] != "0":
        return "0" + digits  # Fallback
    return digits


def build_sms_body(row: dict) -> str:
    order_number = _get(row, "order number", "order_number", "ORDER NUMBER", "Order Number")
    name = _get(row, "name", "NAME", "Name")
    phone = _get(row, "phone", "PHONE", "Phone")
    alt_phone = _get(row, "alt no", "alt_phone", "ALT NO", "Alt No")
    product = _get(row, "product name", "product_name", "PRODUCT NAME", "Product Name")
    amount = _get(row, "amount", "AMOUNT", "Amount")
    address = _get(row, "address", "ADDRESS", "Address")
    city = _get(row, "city", "CITY", "City")

    phone_parts = []
    if phone:
        phone_parts.append(_ensure_leading_zero(phone))
    if alt_phone:
        phone_parts.append(_ensure_leading_zero(alt_phone))
    phone_line = "/".join(phone_parts) if phone_parts else ""
    location = f"{address}, {city}".strip(", ")

    lines = [
        f"Oda Namba {order_number or '-'}",
        name or "-",
        phone_line or "-",
        product or "-",
        amount or "-",
        location or "-",
    ]
    return "\n".join(lines)
