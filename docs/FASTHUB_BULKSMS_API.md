# FastHub BulkSMS API reference

**Base URL:** `https://bulksms.fasthub.co.tz`  
**OpenAPI:** `/v3/api-docs`

## Send SMS

**POST** `/api/sms/send`

**Request body (application/json):**

```json
{
  "auth": {
    "clientId": "string",
    "clientSecret": "string"
  },
  "messages": [
    {
      "text": "string",
      "msisdn": "string",
      "source": "string",
      "reference": "string",
      "coding": "GSM7"
    }
  ]
}
```

- `msisdn`: recipient phone (E.164, e.g. 255755123456)
- `coding`: `GSM7` (default) or other
- `source`: **required** – sender ID (shortcode or alphanumeric). Set `FASTHUB_SOURCE` in `.env`.
- `reference`: optional reference

**Response 200:**

```json
{
  "status": true,
  "message": "string",
  "data": {},
  "balance": 0.1
}
```

## DLR callback (delivery reports)

Register a **callback URL** with FastHub so they POST delivery status updates to your app.

**Messo callback endpoint:** `POST {BASE_URL}/webhook/fasthub/dlr`

- Set `BASE_URL` in `.env` to your public URL (e.g. `https://your-app.com`).
- In FastHub portal / API settings, set the DLR callback URL to:  
  `https://your-app.com/webhook/fasthub/dlr`
- The endpoint accepts JSON or form-encoded bodies, logs the payload, and returns `200 {"received": true}`.
- Optional: `GET {BASE_URL}/webhook/fasthub/dlr/receipts?limit=50` returns the last received receipts (for debugging).

## Other FastHub endpoints

- **POST** `/api/account/balance` – auth only, returns balance
- **POST** `/api/dlr/request/polling/handler` – delivery receipt polling
- **POST** `/api/sms/poll` – poll for receipts
