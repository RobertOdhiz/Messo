from __future__ import annotations

import csv
import io
import logging
import re
from urllib.parse import unquote_plus

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.services import build_sms_body, send_sms as do_send_sms
from app.services.validate_row import (
    get_agent_phone_from_row,
    validate_row,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["send-sms"])

# Success: close after 6 seconds. Error: do not auto-close so users can read (especially empty fields).
SUCCESS_CLOSE_MS = 6000
ERROR_CLOSE_MS = 0
ROUTE_BUILD_ID = "2026-02-18-csvpipe-rawquery-debug"


def _console_log_before_send(row: dict, recipient: str, body: str) -> None:
    """Print parsed row and built message to console so it's visible in uvicorn output."""
    import json as _json
    def _mask(s: str) -> str:
        s = str(s or "").strip()
        d = "".join(c for c in s if c.isdigit())
        return f"...{d[-4:]}" if len(d) >= 4 else s
    safe_row = {}
    for k, v in row.items():
        val = str(v or "").strip()
        if k in ("phone", "alt no", "alt_no", "agent phone", "agent_phone"):
            safe_row[k] = _mask(val)
        else:
            safe_row[k] = val[:80] + "…" if len(val) > 80 else val
    print("\n--- send-sms: parsed row (sanitized) ---")
    print(_json.dumps(safe_row, indent=2, ensure_ascii=False))
    print("--- recipient (msisdn) ---")
    print(recipient)
    print("--- built SMS body ---")
    print(body)
    print("--- end ---\n")


def _normalize_key(s: str) -> str:
    if not s or not isinstance(s, str):
        return ""
    # Replace any whitespace (including \\r, \\n, non-breaking space) and underscores with single space
    s = re.sub(r"[\s_\u00a0]+", " ", s).strip().lower()
    return s


def _row_from_query_params(query_params: dict) -> dict:
    """Build row dict from query string; keys normalized (lowercase, spaces)."""
    row = {}
    for key, value in query_params.items():
        k = _normalize_key(key)
        if k and value is not None:
            row[k] = value.strip() if isinstance(value, str) else str(value)
    return row


def _row_from_csv_string(csv_string: str) -> dict | None:
    """
    Parse CSV string (header row + one data row); return dict keyed by normalized headers.
    Supports:
    - Pipe-delimited: "HEADER1|HEADER2|...\\nvalue1|value2|..." (use in Sheets with TEXTJOIN("|",...))
    - Comma-delimited: standard CSV with optional quoting
    """
    try:
        decoded = unquote_plus(csv_string.strip())
    except Exception:
        return None
    if not decoded:
        return None
    # Normalize line endings (\\n, \\r\\n, \\r) so we always get exactly 2 lines
    decoded = decoded.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in decoded.split("\n") if ln.strip()]
    if len(lines) < 2:
        return None

    # Pipe-delimited (headers and row; use TEXTJOIN("|", FALSE, ...) in Sheets so column count matches)
    if "|" in lines[0]:
        headers = [h.strip() for h in lines[0].split("|")]
        values = [v.strip() for v in lines[1].split("|")]
        # Align lengths: if TEXTJOIN skipped empty cells, pad values so we don't misalign
        if len(values) < len(headers):
            values = values + [""] * (len(headers) - len(values))
        elif len(values) > len(headers):
            values = values[: len(headers)]
        row = {}
        for i, h in enumerate(headers):
            if h:
                k = _normalize_key(h)
                row[k] = values[i] if i < len(values) else ""
        return row

    # Comma-delimited CSV
    reader = csv.reader(io.StringIO(decoded))
    headers = next(reader)
    values = next(reader, None)
    if values is None:
        return None
    row = {}
    for i, h in enumerate(headers):
        k = _normalize_key(h)
        v = values[i].strip() if i < len(values) else ""
        row[k] = v
    return row


def _html_result(
    *,
    success: bool,
    detail: str,
    recipient: str | None = None,
    empty_fields: list[str] | None = None,
    close_after_ms: int = 0,
    debug_build: str | None = None,
) -> str:
    status_text = "SMS sent successfully" if success else "Failed to send SMS"
    detail_text = f"To: {recipient}" if success and recipient else detail
    card_class = "success" if success else "error"

    empty_block = ""
    if empty_fields:
        empty_block = (
            '<p class="empty-fields">Missing or empty fields:</p>'
            '<ul class="empty-list">'
            + "".join(f"<li>{f}</li>" for f in empty_fields)
            + "</ul>"
        )

    close_script = ""
    if close_after_ms > 0:
        close_script = f'<script>setTimeout(function(){{ window.close(); }}, {close_after_ms});</script>'

    build_block = ""
    if debug_build:
        build_block = f'<div class="detail">build: {debug_build}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SMS - {"Sent" if success else "Failed"}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; min-height: 100vh;
      display: flex; align-items: center; justify-content: center; background: #f5f5f5; }}
    .card {{ background: #fff; padding: 2rem; border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08); text-align: left; max-width: 420px; }}
    .status {{ font-size: 1.1rem; margin-bottom: 0.5rem; font-weight: 600; }}
    .detail {{ font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem; }}
    .success .status {{ color: #059669; }}
    .error .status {{ color: #dc2626; }}
    .empty-fields {{ margin-top: 1rem; font-weight: 600; color: #374151; }}
    .empty-list {{ margin: 0.25rem 0 0 1.25rem; padding: 0; color: #dc2626; }}
  </style>
</head>
<body>
  <div class="card {card_class}">
    <div class="status">{status_text}</div>
    <div class="detail">{detail_text}</div>
    {empty_block}
    {build_block}
  </div>
  {close_script}
</body>
</html>"""


@router.get("/send-sms", response_class=HTMLResponse)
def send_sms_page(request: Request):
    """
    GET /send-sms with row data in one of two ways:

    1) CSV param: ?csv=URL_ENCODED_CSV
       CSV = first line headers, second line values (e.g. from Google Sheet).

    2) Query params: ?NAME=...&PHONE=...&AGENT_PHONE=... etc.
       All query params become the row (keys normalized). Use column headers as param names.

    Validates required fields (NAME, PHONE or ALT NO, PRODUCT NAME, AMOUNT, ADDRESS, CITY, AGENT PHONE).
    Success: window closes after 6 seconds. Error: window stays open and shows empty/missing fields.
    """
    query_params = dict(request.query_params)
    debug = str(query_params.get("debug", "")).strip().lower() in ("1", "true", "yes")
    query_params.pop("debug", None)
    dbg_build = ROUTE_BUILD_ID if debug else None

    # Prefer CSV if present. Parse from raw query string so newlines in the value are not truncated.
    csv_raw = None
    if request.url.query and "csv=" in request.url.query:
        raw = request.url.query
        idx = raw.find("csv=")
        if idx != -1:
            csv_raw = raw[idx + 4 :].split("&")[0]
    if not csv_raw:
        csv_raw = query_params.pop("csv", None)
    if csv_raw:
        row = _row_from_csv_string(csv_raw)
        if not row:
            return HTMLResponse(
                _html_result(
                    success=False,
                    detail="Invalid or incomplete CSV. Use header row and one data row.",
                    close_after_ms=ERROR_CLOSE_MS,
                    debug_build=dbg_build,
                )
            )
    else:
        if not query_params:
            return HTMLResponse(
                _html_result(
                    success=False,
                    detail="Missing data. Send ?csv=... or query params (e.g. NAME, PHONE, AGENT_PHONE).",
                    close_after_ms=ERROR_CLOSE_MS,
                    debug_build=dbg_build,
                )
            )
        row = _row_from_query_params(query_params)

    valid, empty_fields = validate_row(row)
    if not valid:
        logger.info(
            "send-sms validation failed; keys=%s has_name=%s has_phone=%s has_alt_no=%s has_product=%s has_amount=%s has_address=%s has_city=%s has_agent_phone=%s",
            sorted(list(row.keys())),
            bool(row.get("name")),
            bool(row.get("phone")),
            bool(row.get("alt no")) or bool(row.get("alt_no")),
            bool(row.get("product name")) or bool(row.get("product_name")),
            bool(row.get("amount")),
            bool(row.get("address")),
            bool(row.get("city")),
            bool(row.get("agent phone")) or bool(row.get("agent_phone")),
        )
        detail = "Cannot send SMS: some required fields are missing or empty."
        if debug:
            # Show which fields were detected (helps debug Google Sheet column mapping).
            detected = {
                "name": bool(row.get("name")),
                "phone": bool(row.get("phone")),
                "alt no": bool(row.get("alt no")) or bool(row.get("alt_no")),
                "product name": bool(row.get("product name")) or bool(row.get("product_name")),
                "amount": bool(row.get("amount")),
                "address": bool(row.get("address")),
                "city": bool(row.get("city")),
                "agent phone": bool(row.get("agent phone")) or bool(row.get("agent_phone")),
            }
            sample = {
                "name": row.get("name", ""),
                "phone": row.get("phone", ""),
                "alt no": row.get("alt no", row.get("alt_no", "")),
                "product name": row.get("product name", row.get("product_name", "")),
                "amount": row.get("amount", ""),
                "address": row.get("address", ""),
                "city": row.get("city", ""),
                "agent phone": row.get("agent phone", row.get("agent_phone", "")),
            }
            # Mask phone-like fields to last 4 digits
            def _mask(v: str) -> str:
                s = str(v or "").strip()
                digits = "".join(c for c in s if c.isdigit())
                if len(digits) >= 4:
                    return f"...{digits[-4:]}"
                return s
            sample["phone"] = _mask(sample["phone"])
            sample["alt no"] = _mask(sample["alt no"])
            sample["agent phone"] = _mask(sample["agent phone"])
            detail += f" (debug: build={ROUTE_BUILD_ID}, detected={detected}, sample={sample}, keys={sorted(list(row.keys()))})"
        return HTMLResponse(
            _html_result(
                success=False,
                detail=detail,
                empty_fields=empty_fields,
                close_after_ms=ERROR_CLOSE_MS,
                debug_build=dbg_build,
            )
        )

    recipient = get_agent_phone_from_row(row)
    body = build_sms_body(row)
    # Console: show parsed row and body before sending
    _console_log_before_send(row, recipient, body)
    success, msg = do_send_sms(recipient, body)

    if not success:
        return HTMLResponse(
            _html_result(
                success=False,
                detail=msg,
                recipient=recipient,
                close_after_ms=ERROR_CLOSE_MS,
                debug_build=dbg_build,
            )
        )

    return HTMLResponse(
        _html_result(
            success=True,
            detail=msg,
            recipient=recipient,
            close_after_ms=SUCCESS_CLOSE_MS,
            debug_build=dbg_build,
        )
    )
