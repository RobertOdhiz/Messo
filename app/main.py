from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile
from fastapi.responses import PlainTextResponse

from app.config import DATA_CSV_PATH
from app.routers import send_sms, webhook
from app.services import ingest_csv

APP_BUILD_ID = "2026-02-18-sqlite-dlr-csvpipe-rawquery"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite and run migrations on startup
    try:
        from app.db import run_migrations
        run_migrations()
    except Exception as e:
        print(f"DB migrations: {e}")
    if DATA_CSV_PATH:
        try:
            from app.services.row_store import ingest_csv_file
            n = ingest_csv_file(DATA_CSV_PATH)
            print(f"Loaded {n} rows from {DATA_CSV_PATH}")
        except Exception as e:
            print(f"Could not load CSV from {DATA_CSV_PATH}: {e}")
    yield


app = FastAPI(
    title="Messo SMS",
    description="Send SMS from CSV/Sheet data via FastHub",
    lifespan=lifespan,
)

app.include_router(send_sms.router)
app.include_router(webhook.router)

@app.get("/version")
def version():
    return {"build": APP_BUILD_ID}


@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"


@app.post("/ingest-csv")
def ingest_csv_upload(file: UploadFile):
    """Upload a CSV file to load rows. Uses 1-based row index (first data row = 1)."""
    content = file.file.read()
    try:
        n = ingest_csv(content)
        return {"ok": True, "rows_loaded": n}
    except Exception as e:
        return {"ok": False, "error": str(e)}
