"""
Validate row data for SMS: required fields must be non-empty.
Returns (is_valid, list of empty/missing field display names).
"""

from __future__ import annotations

import re
from typing import Any, List, Tuple

# Keys we check (normalized: lowercase, spaces -> single space). Display name for errors.
REQUIRED_FOR_MESSAGE = [
    ("name", "NAME"),
    ("product name", "PRODUCT NAME"),
    ("amount", "AMOUNT"),
]
def _normalize_key(s: str) -> str:
    return re.sub(r"[_\s]+", " ", s).strip().lower()


def _get(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    # Fallback: find first key that contains all words (e.g. "product name" vs "product name ")
    return ""


def _get_by_contains(row: dict, *substrings: str) -> str:
    """Get value from row where key contains all given substrings (e.g. 'agent' and 'phone')."""
    want = [s.lower() for s in substrings]
    for k, v in row.items():
        if v is None or not str(v).strip():
            continue
        k_lower = (k or "").lower()
        if all(s in k_lower for s in want):
            return str(v).strip()
    return ""


def validate_row(row: dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check that all required fields are present and non-empty.
    Returns (valid, list of empty field display names).
    """
    empty: List[str] = []

    for key_variants, display in REQUIRED_FOR_MESSAGE:
        keys = [key_variants, key_variants.replace(" ", "_")]
        if not _get(row, *keys):
            empty.append(display)

    # Recipient (AGENT PHONE, comma/semicolon-separated for multiple)
    if not get_agent_phones_from_row(row):
        empty.append("AGENT PHONE")

    # At least one phone (PHONE or ALT NO)
    has_phone = bool(
        _get(row, "phone", "PHONE", "Phone")
        or _get(row, "alt no", "ALT NO", "alt_phone", "Alt No")
    )
    if not has_phone:
        empty.append("PHONE or ALT NO (at least one)")

    return (len(empty) == 0, empty)


def get_agent_phones_from_row(row: dict[str, Any]) -> List[str]:
    """
    Return list of agent phone numbers (recipients) from row.
    AGENT PHONE can be slash-separated for multiple recipients (e.g. 255xxx/255yyy).
    """
    raw = ""
    for k in ("agent phone", "agent_phone", "AGENT PHONE", "Agent Phone"):
        v = row.get(k)
        if v is not None and str(v).strip():
            raw = str(v).strip()
            break
    if not raw:
        raw = _get_by_contains(row, "agent", "phone")
    if not raw:
        return []

    # Split on slash, strip, filter empty
    parts = raw.split("/")
    return [p.strip() for p in parts if p.strip()]


def get_agent_phone_from_row(row: dict[str, Any]) -> str:
    """Return first agent phone (backward compatibility)."""
    phones = get_agent_phones_from_row(row)
    return phones[0] if phones else ""
