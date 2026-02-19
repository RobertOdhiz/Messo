# Send SMS JSON API

**POST** `/send-sms/json`

Accepts JSON body with key-value pairs (no URL length limit). Returns FastHub response for each recipient.

## Request

```http
POST /send-sms/json
Content-Type: application/json

{
  "ORDER NUMBER": "ADGT1775",
  "AMOUNT": "70,000",
  "NAME": "Rodrick mzopole",
  "ADDRESS": "ileje p o box 124",
  "PHONE": "753699004",
  "ALT NO": "",
  "COUNTRY": "TANZANIA",
  "CITY": "TUNDUMA",
  "PRODUCT NAME": "1 PACK OF INFECTION TEA 70,000TZS",
  "AGENT PHONE": "0651359693/0748415123"
}
```

Keys are normalized (case, spaces). AGENT PHONE can be slash-separated for multiple recipients.

## Response (success)

```json
{
  "success": true,
  "message": "Sent to 2/2 recipient(s)",
  "results": [
    {
      "msisdn": "255651359693",
      "success": true,
      "message": "sent (balance: 0.5) (ref: abc123)",
      "fasthub": {
        "status": true,
        "message": "sent",
        "data": {},
        "balance": 0.5
      }
    },
    {
      "msisdn": "255748415123",
      "success": true,
      "message": "sent (balance: 0.4) (ref: def456)",
      "fasthub": {
        "status": true,
        "message": "sent",
        "data": {},
        "balance": 0.4
      }
    }
  ]
}
```

## Response (failure)

```json
{
  "success": false,
  "message": "Validation failed",
  "empty_fields": ["AGENT PHONE"],
  "fasthub": null
}
```

Or when FastHub returns an error:

```json
{
  "success": false,
  "message": "Sent to 1/2 recipient(s)",
  "results": [
    {
      "msisdn": "255651359693",
      "success": true,
      "message": "sent (ref: abc123)",
      "fasthub": { "status": true, "message": "sent", "data": {}, "balance": 0.5 }
    },
    {
      "msisdn": "255748415123",
      "success": false,
      "message": "Validation errors (ref: def456, details: [{...}])",
      "fasthub": {
        "status": false,
        "message": "Validation errors",
        "data": [{"source": " is missing but it is required"}],
        "balance": null
      }
    }
  ]
}
```
