# SMS Automation API – High-Level Design Overview

## Goal

Build a **FastAPI service** that sits between your data source (CSV / Google Sheet) and **FastHub’s SMS API**. When someone clicks a link (e.g. in a Google Sheet), the request hits your API, which builds the message from the row data and sends it via FastHub to the recipient.

---

## Data Model (per row)

| Field to extract | Source column(s) | Example |
|------------------|------------------|--------|
| Customer name    | NAME             | Cosmas mhapu |
| Customer phone   | PHONE / ALT NO   | 769563531 or 623514831 |
| Product name     | PRODUCT NAME     | Performax Tea |
| Price            | AMOUNT           | 60000 |
| Address + City   | ADDRESS, CITY    | njombe-makambako, Tanzania |
| **Agent phone**  | **AGENT PHONE** (new column) | e.g. 755123456 |

The **AGENT PHONE** column is the number that will receive the SMS (e.g. delivery agent or call center agent for that row).

---

## Architecture (FastAPI as “in-between”)

```
┌─────────────────┐      ┌──────────────────────────────┐      ┌─────────────────┐
│  Google Sheet   │      │  Your FastAPI service        │      │  FastHub SMS    │
│  (or CSV)       │ ───► │  (messo)                     │ ───► │  API            │
│                 │      │                              │      │                 │
│  • Row data     │      │  • Receive “send” request   │      │  • Send SMS     │
│  • “Send SMS”   │      │  • Resolve row (id/token)   │      │  • Return       │
│    link         │      │  • Build message from row   │      │    status       │
└─────────────────┘      │  • Call FastHub API         │      └─────────────────┘
                         │  • Return success/failure   │
                         └──────────────────────────────┘
```

- **Data source**: Google Sheet (with a “Send SMS” link per row) or a CSV that you upload/import into the system.
- **Your API**: Receives the “send” request, gets the row data, formats the SMS body, and calls FastHub.
- **FastHub**: Sends the actual SMS and returns delivery status (as far as their API supports).

---

## Core flow

1. **User clicks link in sheet**  
   Link points to your API, e.g.:  
   `https://your-api.com/send-sms?row_id=abc123` or `.../send-sms?token=xyz789`

2. **FastAPI receives request**  
   - Validates API key or token (so random people can’t trigger sends).  
   - Uses `row_id` or `token` to identify which row to use.

3. **Resolve row data**  
   - **Option A – Data in your API**: CSV (or sheet) is imported/stored in your service; you look up by `row_id` (or by a stable row index).  
   - **Option B – Data in Google Sheet**: Your API calls Google Sheets API with the sheet ID + row index (or a key column) to fetch that row’s cells.  
   - **Option C – Data in request**: The link includes enough query params (e.g. phone, name, product, …) so the API doesn’t need to store or fetch the sheet; it only validates a signed token and then uses the params.  
   Choose one of these based on whether you prefer to store data in your backend or keep it only in the sheet.

4. **Build message**  
   From the row you build a single SMS body, e.g.:  
   - Customer: &lt;name&gt;  
   - Phone: &lt;phone&gt; / &lt;alt phone&gt;  
   - Product: &lt;product name&gt;  
   - Price: &lt;amount&gt;  
   - Address: &lt;address&gt;, &lt;city&gt;  

   Recipient = **AGENT PHONE** for that row.

5. **Call FastHub API**  
   - One HTTP request to FastHub’s send-SMS endpoint (exact URL and parameters to be taken from their docs or support).  
   - Typical pattern: API key, destination number (agent phone), message body.  
   - Map their response to a simple success/error and optional delivery status.

6. **Respond to client**  
   Return JSON (and optionally a simple HTML “Message sent” / “Error” page so the link can be opened in a browser).

---

## Suggested FastAPI structure

- **`/send-sms`** (GET)  
  - Query params: `row_id` or `token` (and optionally `sheet_id` + `row_index` if you use Option B).  
  - **Returns HTML page** (not JSON) that:
    - Shows "Sending SMS..." progress indicator
    - Processes the send synchronously (calls FastHub API)
    - Displays success ✅ or error ❌ message with details
    - Auto-closes window after 2-3 seconds using JavaScript
  - This allows clicking the link in Google Sheets to open a browser window that shows progress and closes automatically.

- **`/api/send-sms`** (optional, POST)  
  - JSON API endpoint for programmatic access (if needed for Apps Script or other integrations).  
  - Returns: `{ "success": true/false, "message": "...", "recipient": "...", "fasthub_id": "..." }`.

- **`/health`**  
  - For uptime checks; no auth.

- **Optional**:  
  - **`/ingest-csv`** – Upload CSV, parse and store rows with internal `row_id` (for Option A).  
  - **`/webhook/fasthub`** – If FastHub supports delivery callbacks, receive status updates and store or log them.

Config (env vars):

- FastHub API base URL, API key (or username/password if they use that).  
- Optional: Google Sheets API credentials (if Option B).  
- Optional: Secret for signing/verifying `token` in links (if Option C).

---

## Google Sheet “link” behavior

**Recommended: Hyperlink formula in every row**

Add a new column (e.g., "SEND SMS") with a formula like:

```
=HYPERLINK("https://your-api.com/send-sms?row_index=" & ROW() & "&sheet_id=YOUR_SHEET_ID", "📤 Send SMS")
```

Or if you have a stable row identifier (e.g., ORDER NUMBER in column B):

```
=HYPERLINK("https://your-api.com/send-sms?order_number=" & B2, "📤 Send SMS")
```

**What happens when clicked:**

1. Browser opens a new window/tab pointing to your FastAPI `/send-sms` endpoint
2. FastAPI processes the request synchronously:
   - Shows HTML with "Sending SMS..." spinner
   - Fetches row data (from sheet or your storage)
   - Builds message
   - Calls FastHub API
3. HTML page updates to show:
   - ✅ Success: "SMS sent successfully to [AGENT PHONE]"
   - ❌ Error: "Failed to send SMS: [error details]"
4. After 2-3 seconds, JavaScript automatically closes the window: `setTimeout(() => window.close(), 2500)`

**Alternative: Apps Script button**  
If you prefer a button instead of a link, use Apps Script that opens the same URL in a popup window. The behavior is the same—the HTML page handles progress and auto-close.

- **Option 1 – Hyperlink formula** (deprecated - use recommended approach above)  
  In a cell: `=HYPERLINK("https://your-api.com/send-sms?row_id=" & A2, "Send SMS")`  
  Assumes you have a stable row identifier in column A (or you use row number and pass it as `row_index`).

- **Option 2 – Apps Script**  
  A button or menu that, for the active row, reads the row data (and AGENT PHONE), calls your FastAPI `/send-sms` (with row index or a row key), and shows “Sent” or an error.  
  Here the “link” is the button; the actual HTTP call is from Apps Script to your API.

- **Option 3 – Pre-signed link**  
  Your backend (or a small script) generates links with a signed token that encodes row_id (and optionally the payload). The link only works once or for a limited time.  
  Good if you don’t want to expose raw row IDs.

---

## Security and robustness

- **Auth**: Require an API key or signed token on `/send-sms` so only your sheet/script can trigger sends.  
- **Rate limiting**: Optional per-IP or per-key limits to avoid abuse.  
- **Idempotency**: Optional idempotency key (e.g. `row_id + date`) so double-clicks don’t send twice.  
- **Logging**: Log every send (recipient, row_id, success/failure, FastHub response) for support and auditing.  
- **Secrets**: Keep FastHub API key and Google credentials in env vars or a secrets manager, not in code.

---

## Implementation order (after you approve this design)

1. **FastAPI app** – Project setup, `/health`, `/send-sms` endpoint that returns HTML template.  
2. **HTML template** – Create a progress page template (spinner, success/error states, auto-close script).  
3. **Row data resolution** – Implement one of Option A/B/C (e.g. CSV in memory or DB, or Google Sheets client).  
4. **Message builder** – Map your columns (NAME, PHONE, ALT NO, PRODUCT NAME, AMOUNT, ADDRESS, CITY, AGENT PHONE) to the SMS template.  
5. **FastHub client** – HTTP client for their send-SMS endpoint (you may need to get exact API docs from FastHub).  
6. **Wire `/send-sms`** – Resolve row → build message → call FastHub → render HTML with result → auto-close.  
7. **Google Sheet** – Add AGENT PHONE column and HYPERLINK formula in "SEND SMS" column for each row.  
8. **Optional** – CSV upload/ingest, webhook, idempotency, rate limiting.

---

## Open points

- **FastHub API**: Exact endpoint, auth (API key vs username/password), and request/response format need to be confirmed (e.g. from FastHub support or portal). The design assumes a simple “send SMS” HTTP API.  
- **Data source**: Decide whether you want data stored in your API (CSV/DB) or always read from Google Sheets (Option A vs B vs C above).  
- **Message template**: Final wording and length (SMS character limit) can be tuned once the builder is in place.

If this high-level design matches what you have in mind, next step is to implement the FastAPI app and the FastHub client; we can stub the FastHub call until you have the exact API details.
