from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db import Base


class DlrReceipt(Base):
    """Delivery report from FastHub (or other provider) webhook."""

    __tablename__ = "dlr_receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    received_at = Column(DateTime, server_default=func.now())
    body_json = Column(Text, default="")
    raw_body = Column(Text, default="")
    status = Column(String(64), default="")
    msisdn = Column(String(32), default="")
    reference_id = Column(String(128), default="")


class SentSms(Base):
    """Audit log of sent SMS."""

    __tablename__ = "sent_sms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now())
    recipient = Column(String(32), nullable=False)
    message_preview = Column(String(256), default="")
    provider = Column(String(32), default="")
    success = Column(Integer, default=1)
    detail = Column(Text, default="")
