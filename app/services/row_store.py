"""
In-memory row store. Rows are keyed by 1-based row_index (sheet-style).
CSV is ingested via ingest_csv(); column headers are normalized for lookup.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

_rows: dict[int, dict[str, Any]] = {}
_header_map: dict[str, str] = {}  # normalized -> original


def _normalize_key(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _row_from_raw(headers: list[str], values: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i, h in enumerate(headers):
        key = _normalize_key(h)
        out[key] = values[i].strip() if i < len(values) else ""
    return out


def ingest_csv(content: str | bytes | io.TextIO) -> int:
    """Parse CSV and store rows. Returns number of rows stored. Keys by 1-based row index (first data row = 1)."""
    global _rows, _header_map
    _rows.clear()

    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    if isinstance(content, str):
        content = io.StringIO(content)

    reader = csv.reader(content)
    headers = next(reader, None)
    if not headers:
        return 0

    count = 0
    for idx, row_values in enumerate(reader):
        row_index = idx + 1
        row = _row_from_raw(headers, row_values)
        _rows[row_index] = row
        count += 1
    return count


def ingest_csv_file(path: str) -> int:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return ingest_csv(f)


def get_row(row_index: int) -> dict[str, Any] | None:
    """Get row by 1-based row index. Returns None if not found."""
    return _rows.get(row_index)


def get_agent_phone(row: dict[str, Any]) -> str:
    """Extract recipient (AGENT PHONE) from row."""
    for k in ("agent phone", "agent_phone", "AGENT PHONE", "Agent Phone"):
        v = row.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def get_row_by_order_number(order_number: str) -> dict[str, Any] | None:
    """Find first row whose order number matches. Column may be 'order number', 'ORDER NUMBER', etc."""
    key = _normalize_key("order number")
    for row in _rows.values():
        val = row.get(key) or row.get("ORDER NUMBER") or row.get("order_number")
        if val is not None and str(val).strip() == str(order_number).strip():
            return row
    return None


def list_row_ids() -> list[int]:
    """List all stored 1-based row indices."""
    return sorted(_rows.keys())


def row_count() -> int:
    return len(_rows)
