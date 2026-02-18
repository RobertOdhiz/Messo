"""
BulkSMS.com JSON REST API v1 client.
Docs: https://www.bulksms.com/developer/json/v1/
Auth: API Token + Secret (Basic auth).
"""

from __future__ import annotations

import logging

import httpx

from app.config import BULKSMS_BASE_URL, BULKSMS_SECRET, BULKSMS_TOKEN

logger = logging.getLogger(__name__)


def send_sms(to_phone: str, message: str) -> tuple[bool, str]:
    """
    Send SMS via BulkSMS.com API.
    POST /messages with JSON { "to": "+...", "body": "..." }.
    Returns (success, detail_message).
    """
    if not BULKSMS_TOKEN or not BULKSMS_SECRET:
        logger.warning("BULKSMS_TOKEN or BULKSMS_SECRET not set; skipping send")
        return False, "BulkSMS not configured (set BULKSMS_TOKEN and BULKSMS_SECRET)"

    to_phone = _normalize_phone(to_phone)
    if not to_phone:
        return False, "Invalid recipient phone number"

    url = f"{BULKSMS_BASE_URL}/messages"
    payload = {"to": to_phone, "body": message}
    auth = (BULKSMS_TOKEN, BULKSMS_SECRET)

    try:
        resp = httpx.post(
            url,
            json=payload,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )

        if resp.status_code == 200:
            data = resp.json() if resp.content else {}
            # API may return a single message object or a list
            if isinstance(data, list) and data:
                msg_id = data[0].get("id") or data[0].get("message_id", "sent")
            elif isinstance(data, dict):
                msg_id = data.get("id") or data.get("message_id", "sent")
            else:
                msg_id = "sent"
            return True, str(msg_id)

        # Error response
        try:
            err = resp.json()
            code = err.get("code", "")
            err_msg = err.get("message", resp.text)
            return False, f"{code}: {err_msg}" if code else err_msg
        except Exception:
            return False, f"HTTP {resp.status_code}: {resp.text}"

    except httpx.TimeoutException:
        return False, "Request timed out"
    except httpx.RequestError as e:
        logger.exception("BulkSMS request failed")
        return False, str(e)
    except Exception as e:
        logger.exception("BulkSMS send failed")
        return False, str(e)


def _normalize_phone(s: str) -> str:
    """E164-style: digits and leading +; add country code if 9 digits and no prefix."""
    s = "".join(c for c in s if c.isdigit() or c == "+")
    if not s:
        return ""
    if s.startswith("+"):
        return s
    # Tanzania 255, South Africa 27, etc.
    if len(s) >= 9 and not s.startswith("255") and not s.startswith("27"):
        return "255" + s.lstrip("0")  # default Tanzania
    return s
