from .message_builder import build_sms_body
from .row_store import get_row, get_row_by_order_number, ingest_csv, list_row_ids
from .bulksms import send_sms as bulksms_send_sms
from .fasthub import send_sms as fasthub_send_sms


def send_sms(to_phone: str, message: str) -> tuple[bool, str]:
    """Send SMS via BulkSMS (if configured), else FastHub, else stub."""
    from app.config import (
        BULKSMS_SECRET,
        BULKSMS_TOKEN,
        FASTHUB_CLIENT_ID,
        FASTHUB_CLIENT_SECRET,
    )
    if BULKSMS_TOKEN and BULKSMS_SECRET:
        return bulksms_send_sms(to_phone, message)
    if FASTHUB_CLIENT_ID and FASTHUB_CLIENT_SECRET:
        return fasthub_send_sms(to_phone, message)
    return fasthub_send_sms(to_phone, message)  # stub when no provider set


__all__ = [
    "build_sms_body",
    "get_row",
    "get_row_by_order_number",
    "ingest_csv",
    "list_row_ids",
    "send_sms",
    "bulksms_send_sms",
    "fasthub_send_sms",
]
