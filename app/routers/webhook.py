"""
Webhook endpoints for SMS providers (e.g. FastHub DLR / delivery receipts).
Register the callback URL with the provider so they POST delivery status updates here.
Persists to SQLite (dlr_receipts table).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.base import DlrReceipt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/fasthub", tags=["webhook"])


def _parse_body(content_type: str, raw_str: str) -> dict:
    body = {}
    try:
        if "application/json" in content_type and raw_str.strip():
            body = json.loads(raw_str)
        elif raw_str.strip():
            body = parse_qs(raw_str)
            body = {k: v[0] if len(v) == 1 else v for k, v in body.items()}
    except Exception as e:
        logger.warning("DLR callback parse failed: %s", e)
    return body


@router.post("/dlr")
async def fasthub_dlr_callback(request: Request, db: Session = Depends(get_db)):
    """
    FastHub BulkSMS delivery report (DLR) callback.
    Register this URL with FastHub so they POST delivery status updates here.
    Callback URL: {BASE_URL}/webhook/fasthub/dlr

    Accepts JSON or form-encoded body. Persists to SQLite and returns 200.
    """
    raw = await request.body()
    raw_str = raw.decode("utf-8", errors="replace")
    content_type = request.headers.get("content-type", "")
    body = _parse_body(content_type, raw_str)

    logger.info("FastHub DLR callback: %s", body if body else raw_str)

    # Persist to SQLite
    receipt = DlrReceipt(
        body_json=json.dumps(body) if body else "",
        raw_body=raw_str[:65535] if raw_str else "",
        status=str(body.get("status", ""))[:64] if isinstance(body, dict) else "",
        msisdn=str(body.get("msisdn", ""))[:32] if isinstance(body, dict) else "",
        reference_id=str(body.get("reference_id", body.get("reference", "")))[:128] if isinstance(body, dict) else "",
    )
    db.add(receipt)
    db.commit()

    return JSONResponse({"received": True}, status_code=200)


@router.get("/dlr/receipts")
async def list_dlr_receipts(limit: int = 50, db: Session = Depends(get_db)):
    """Return the last delivery receipts from SQLite (for debugging). Max 50 per request."""
    n = min(max(1, limit), 100)
    rows = db.query(DlrReceipt).order_by(DlrReceipt.id.desc()).limit(n).all()
    receipts = []
    for r in rows:
        try:
            body = json.loads(r.body_json) if r.body_json else {}
        except Exception:
            body = {}
        receipts.append({
            "id": r.id,
            "received_at": r.received_at.isoformat() if r.received_at else None,
            "status": r.status,
            "msisdn": r.msisdn,
            "reference_id": r.reference_id,
            "body": body,
        })
    return {"receipts": receipts, "count": len(receipts)}
