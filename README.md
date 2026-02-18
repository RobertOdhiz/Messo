# Messo – SMS automation

Sends SMS from CSV/Sheet data via **BulkSMS.com** (or FastHub). Click a link → message is sent to the agent phone; page shows progress and closes.

## Message format (exactly)

```
<Customer name>
<Customer phone>/<Alt Phone>
<Product Name>
<Price of Product>
<Address>, <City>
```

## Setup

```bash
cd /Users/robert/Projects/FulfillmentEA/messo
python3 -m pip install -r requirements.txt
cp .env.example .env   # set BULKSMS_TOKEN and BULKSMS_SECRET (or FastHub vars)
```

## Run

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Load data (Option A – data in API)

1. **Upload CSV**  
   `POST /ingest-csv` with a CSV file. First row = headers. Columns are normalized (e.g. "ORDER NUMBER", "NAME", "PHONE", "ALT NO", "PRODUCT NAME", "AMOUNT", "ADDRESS", "CITY", "AGENT PHONE").

2. **Or set at startup**  
   In `.env`: `DATA_CSV_PATH=/path/to/orders.csv`  
   The app loads that file on startup.

## Send SMS (no auth)

Row data is sent in the link (no server-side row store needed for this flow).

**Option A – Query params (recommended for Google Sheets)**  
Send each column as a param; use header names (underscores allowed). Example:

```
GET /send-sms?ORDER_NUMBER=MB123&NAME=John&PHONE=755...&ALT_NO=&PRODUCT_NAME=Tea&AMOUNT=60000&ADDRESS=Dar&CITY=Dar es Salaam&AGENT_PHONE=755...
```

**Option B – CSV param**  
One param `csv` = URL-encoded CSV: first line = headers, second line = values.

- **Success:** Window closes after **6 seconds**.
- **Error:** Window **stays open** and shows which fields are missing or empty.

## Google Sheet link (one per row)

Use query params so the row data is sent with the link. Replace column letters to match your sheet (row 1 = headers, row 2 = first data row). Example if ORDER NUMBER=B, AMOUNT=C, NAME=D, ADDRESS=E, PHONE=F, ALT NO=G, CITY=H, PRODUCT NAME=I, AGENT PHONE=N:

```
=HYPERLINK("http://localhost:8000/send-sms?ORDER_NUMBER="&ENCODEURL(B2)&"&AMOUNT="&ENCODEURL(C2)&"&NAME="&ENCODEURL(D2)&"&ADDRESS="&ENCODEURL(E2)&"&PHONE="&ENCODEURL(F2)&"&ALT_NO="&ENCODEURL(G2)&"&CITY="&ENCODEURL(H2)&"&PRODUCT_NAME="&ENCODEURL(I2)&"&AGENT_PHONE="&ENCODEURL(N2), "Send SMS")
```

Required params: **NAME**, **PHONE** or **ALT_NO** (at least one), **PRODUCT_NAME**, **AMOUNT**, **ADDRESS**, **CITY**, **AGENT_PHONE**. Add more columns if you like; they are ignored for the message.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Returns `ok` |
| `GET /send-sms?csv=...` or `?NAME=...&PHONE=...&AGENT_PHONE=...` | Validates row, sends SMS, returns HTML (6s close on success; stays open on error with empty fields listed) |
| `POST /ingest-csv` | Body: CSV file. Loads rows into memory (optional; not needed when using link-with-data). |
| `POST /webhook/fasthub/dlr` | **Callback URL** for FastHub DLR (delivery reports). Register this URL in FastHub; they POST status updates here. |
| `GET /webhook/fasthub/dlr/receipts?limit=50` | Returns last delivery receipts (for debugging). |

## Database (SQLite)

The app uses SQLite by default. On startup it:

- Creates the database file if it doesn't exist (`messo.db` in the project root unless `DATABASE_URL` is set).
- Runs Alembic migrations (`alembic upgrade head`), so new migrations are applied automatically.

To add a new migration:

```bash
alembic revision -m "describe_change"
# Edit alembic/versions/xxx_describe_change.py, then run the app or: alembic upgrade head
```

## Config (.env)

- **BulkSMS.com** (used first if set):  
  `BULKSMS_TOKEN`, `BULKSMS_SECRET` – from [BulkSMS Settings > API Tokens](https://www.bulksms.com); `BULKSMS_BASE_URL` (default `https://api.bulksms.com/v1`).
- **FastHub BulkSMS** (Tanzania, fallback):  
  `FASTHUB_CLIENT_ID`, `FASTHUB_CLIENT_SECRET`; optional `FASTHUB_API_URL` (default `https://bulksms.fasthub.co.tz`), `FASTHUB_SOURCE` (sender ID).
- `DATABASE_URL` – SQLite URL (default `sqlite:///./messo.db`). DB is created and migrated on startup.  
- `DATA_CSV_PATH` – Optional path to CSV to load on startup  
- `BASE_URL` – Base URL for links and **DLR callback** (e.g. `https://your-domain.com`). FastHub will POST delivery reports to `{BASE_URL}/webhook/fasthub/dlr`.  
- `FASTHUB_DLR_CALLBACK_URL` – Override full callback URL (default: `{BASE_URL}/webhook/fasthub/dlr`).

If neither BulkSMS nor FastHub is configured, the app still runs but does not send real SMS (stub response).
