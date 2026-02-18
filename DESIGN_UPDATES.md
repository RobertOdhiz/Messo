# Design Updates: Link-Based SMS Sending with Auto-Close

## Key Requirement
- **Link in every row** of Google Sheet
- When clicked, opens a browser window
- Shows progress while sending
- **Auto-closes** after message is sent

## Updated Flow

### 1. Google Sheet Setup
Add a "SEND SMS" column with HYPERLINK formula in each row:

```
=HYPERLINK("https://your-api.com/send-sms?row_index=" & ROW() & "&sheet_id=YOUR_SHEET_ID", "📤 Send SMS")
```

Or using ORDER NUMBER (if in column B):
```
=HYPERLINK("https://your-api.com/send-sms?order_number=" & B2, "📤 Send SMS")
```

### 2. What Happens When Link is Clicked

1. **Browser opens** → New window/tab navigates to `/send-sms?row_index=X&sheet_id=Y`
2. **FastAPI endpoint** (`/send-sms` GET):
   - Immediately returns HTML page with "Sending SMS..." spinner
   - Processes request synchronously:
     - Fetches row data (from Google Sheets API or your storage)
     - Extracts: NAME, PHONE/ALT NO, PRODUCT NAME, AMOUNT, ADDRESS, CITY, **AGENT PHONE**
     - Builds SMS message
     - Calls FastHub API
   - Updates HTML to show result:
     - ✅ Success: "SMS sent successfully to [AGENT PHONE]"
     - ❌ Error: "Failed to send SMS: [error details]"
3. **Auto-close** → JavaScript closes window after 2-3 seconds:
   ```javascript
   setTimeout(() => window.close(), 2500)
   ```

### 3. HTML Template Structure

The `/send-sms` endpoint returns HTML (not JSON) with:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Sending SMS...</title>
  <style>
    /* Progress spinner, success/error styling */
  </style>
</head>
<body>
  <div id="status">
    <div class="spinner">Sending SMS...</div>
  </div>
  <script>
    // After FastAPI processes and renders result:
    setTimeout(() => window.close(), 2500);
  </script>
</body>
</html>
```

### 4. FastAPI Endpoint Design

**`GET /send-sms`**
- Query params: `row_index`, `sheet_id` (or `order_number`, etc.)
- Returns: `HTMLResponse` (not JSON)
- Process flow:
  1. Validate request (API key/token if needed)
  2. Fetch row data
  3. Build message
  4. Call FastHub API
  5. Render HTML template with result
  6. HTML includes auto-close script

**Optional: `POST /api/send-sms`**
- JSON API for programmatic access (Apps Script, etc.)
- Returns: `{"success": true/false, "message": "...", ...}`

## Benefits

✅ **User-friendly**: Click link → see progress → window closes automatically  
✅ **No manual steps**: No need to check another page or close window manually  
✅ **Clear feedback**: Visual progress indicator and success/error message  
✅ **Works in Google Sheets**: HYPERLINK formula opens browser window automatically

## Implementation Notes

- The HTML page is rendered server-side by FastAPI (using Jinja2 templates)
- The SMS send happens synchronously before rendering the result
- Auto-close uses `window.close()` which works for windows opened by JavaScript/links
- If browser blocks auto-close, user can manually close (message is already sent)
