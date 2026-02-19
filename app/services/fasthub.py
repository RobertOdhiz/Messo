"""
FastHub BulkSMS API client (bulksms.fasthub.co.tz).
API docs: POST /api/sms/send with auth.clientId, auth.clientSecret, messages[].text, messages[].msisdn.
"""

from __future__ import annotations

import logging

import httpx

from app.config import (
    FASTHUB_API_URL,
    FASTHUB_CLIENT_ID,
    FASTHUB_CLIENT_SECRET,
    FASTHUB_SOURCE,
)

logger = logging.getLogger(__name__)


def _log_fasthub_request(url: str, payload: dict, raw_message: str) -> None:
    """Log what we send to FastHub; redact clientSecret. Print to console so it's visible in uvicorn."""
    import json as _json
    safe = {
        "url": url,
        "auth": {
            "clientId": payload.get("auth", {}).get("clientId", ""),
            "clientSecret": _redact_secret(payload.get("auth", {}).get("clientSecret", "")),
        },
        "messages": [],
    }
    for m in payload.get("messages", []):
        text = m.get("text", "")
        safe["messages"].append({
            "msisdn": m.get("msisdn"),
            "source": m.get("source"),
            "reference": m.get("reference"),
            "coding": m.get("coding"),
            "text_preview": (text[:200] + "…") if len(text) > 200 else text,
            "text_len": len(text),
        })
    logger.info("FastHub request: %s", safe)
    # So it shows in uvicorn console
    print("\n--- FastHub request (payload as sent, secret redacted) ---")
    print(_json.dumps(safe, indent=2, ensure_ascii=False))
    print("--- end FastHub request ---\n")


def _redact_secret(s: str) -> str:
    if not s or len(s) <= 4:
        return "***"
    return "***" + s[-4:]


def send_sms_with_response(to_phone: str, message: str) -> dict:
    """
    Send SMS via FastHub BulkSMS API.
    Returns dict: { success, message, fasthub: { status, message, data, balance } }
    """
    if not FASTHUB_CLIENT_ID or not FASTHUB_CLIENT_SECRET:
        logger.warning("FASTHUB_CLIENT_ID or FASTHUB_CLIENT_SECRET not set; skipping send")
        return {
            "success": False,
            "message": "FastHub not configured (set FASTHUB_CLIENT_ID and FASTHUB_CLIENT_SECRET)",
            "fasthub": {"status": False, "message": "Not configured"},
        }

    to_phone = _normalize_phone(to_phone)
    if not to_phone:
        return {
            "success": False,
            "message": "Invalid recipient phone number",
            "fasthub": None,
        }

    url = f"{FASTHUB_API_URL}/api/sms/send"
    reference = _new_reference()
    payload = {
        "auth": {
            "clientId": FASTHUB_CLIENT_ID,
            "clientSecret": FASTHUB_CLIENT_SECRET,
        },
        "messages": [
            {
                "text": message,
                "msisdn": to_phone,
                "coding": "GSM7",
                **({"source": FASTHUB_SOURCE} if FASTHUB_SOURCE else {}),
                "reference": reference,
            }
        ],
    }

    try:
        # Log payload sent to FastHub (redact clientSecret)
        _log_fasthub_request(url, payload, message)
        resp = httpx.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )
        data = {}
        if resp.headers.get("content-type", "").startswith("application/json") and resp.content:
            try:
                data = resp.json()
            except Exception:
                pass

        fasthub_resp = {
            "status": data.get("status"),
            "message": data.get("message"),
            "data": data.get("data"),
            "balance": data.get("balance"),
        }

        if resp.status_code == 200 and data.get("status") is True:
            msg = data.get("message", "sent")
            balance = data.get("balance")
            if balance is not None:
                msg = f"{msg} (balance: {balance})"
            return {
                "success": True,
                "message": f"{msg} (ref: {reference})",
                "fasthub": fasthub_resp,
            }

        # Error
        err_msg = data.get("message", resp.text or f"HTTP {resp.status_code}")
        extra = data.get("data")
        if extra not in (None, "", {}, []):
            try:
                import json as _json
                extra_str = _json.dumps(extra, ensure_ascii=False)
            except Exception:
                extra_str = str(extra)
            if len(extra_str) > 800:
                extra_str = extra_str[:800] + "…"
            err_msg = f"{err_msg} (ref: {reference}, details: {extra_str})"
        else:
            err_msg = f"{err_msg} (ref: {reference})"
        return {
            "success": False,
            "message": err_msg,
            "fasthub": fasthub_resp,
        }

    except httpx.TimeoutException:
        return {"success": False, "message": "Request timed out", "fasthub": None}
    except httpx.RequestError as e:
        logger.exception("FastHub request failed")
        return {"success": False, "message": str(e), "fasthub": None}
    except Exception as e:
        logger.exception("FastHub send failed")
        return {"success": False, "message": str(e), "fasthub": None}


def send_sms(to_phone: str, message: str) -> tuple[bool, str]:
    """Send SMS via FastHub; returns (success, message) for backward compatibility."""
    r = send_sms_with_response(to_phone, message)
    return r["success"], r["message"]


def _normalize_phone(s: str) -> str:
    """E.164-style: digits and leading +; add 255 for Tanzanian 9-digit numbers."""
    s = "".join(c for c in s if c.isdigit() or c == "+")
    if not s:
        return ""
    if s.startswith("+"):
        return s
    if len(s) >= 9 and not s.startswith("255"):
        return "255" + s.lstrip("0")
    return s


def _new_reference() -> str:
    # FastHub API supports a client reference for tracking/DLR polling.
    # Keep it short-ish and URL-safe.
    import uuid

    return uuid.uuid4().hex
