import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# BulkSMS.com JSON API (https://api.bulksms.com/v1) – recommended
BULKSMS_BASE_URL: str = os.getenv("BULKSMS_BASE_URL", "https://api.bulksms.com/v1").rstrip("/")
BULKSMS_TOKEN: str = os.getenv("BULKSMS_TOKEN", "")
BULKSMS_SECRET: str = os.getenv("BULKSMS_SECRET", "")

# FastHub BulkSMS API (Tanzania) – https://bulksms.fasthub.co.tz, POST /api/sms/send
FASTHUB_API_URL: str = os.getenv("FASTHUB_API_URL", "https://bulksms.fasthub.co.tz").rstrip("/")
FASTHUB_CLIENT_ID: str = os.getenv("FASTHUB_CLIENT_ID", "")
FASTHUB_CLIENT_SECRET: str = os.getenv("FASTHUB_CLIENT_SECRET", "")
FASTHUB_SOURCE: str = os.getenv("FASTHUB_SOURCE", "")  # optional sender ID

BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")

# Callback URL for FastHub DLR (delivery reports). If not set, derived from BASE_URL.
FASTHUB_DLR_CALLBACK_URL: str = os.getenv("FASTHUB_DLR_CALLBACK_URL", "").rstrip("/")

# Path to optional default CSV (loaded at startup if set)
DATA_CSV_PATH: str = os.getenv("DATA_CSV_PATH", "")

# SQLite database (created on startup if missing; migrations run automatically)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./messo.db")
