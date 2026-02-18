# Google Sheet: Send SMS link (headers + data)

Use one hyperlink that sends **row 1 (headers)** and **current row (data)**. The server parses them and extracts NAME, PHONE, PRODUCT NAME, AGENT PHONE, etc. by header name, so column order doesn’t matter.

## Formula (one per row)

**Row 2** – replace `http://localhost:8000` with your app URL.  
**Range B:U** = from your first data column (e.g. ORDER NUMBER in B) through **AGENT PHONE** (e.g. in U). Change `B`/`U` if your AGENT PHONE column is elsewhere.

**Use `FALSE` in TEXTJOIN** so empty cells are included and the number of columns matches between header and data rows.

```
=HYPERLINK("http://localhost:8000/send-sms?csv="&ENCODEURL(TEXTJOIN("|",FALSE,$B$1:$U$1)&CHAR(10)&TEXTJOIN("|",FALSE,B2:U2)), "Send SMS")
```

- **Row 2:** use `B2:U2` as above.
- **Row 3:** use `B3:U3` (or put the formula in row 2 and **fill down**; the `2` will become 3, 4, …).
- **Headers** are fixed as `$B$1:$U$1` so every row sends the same header names.

## How it works

1. **Sheet:** `TEXTJOIN("|", TRUE, $B$1:$U$1)` builds the header line (e.g. `ORDER NUMBER|AMOUNT|NAME|...|AGENT PHONE`). `TEXTJOIN("|", TRUE, B2:U2)` builds the data line for that row. `CHAR(10)` is the newline between them.
2. **URL:** `csv=` + `ENCODEURL(...)` sends that as one parameter.
3. **Server:** Receives the string, splits by newline then by `|`, matches headers to values, and normalizes keys (e.g. `AGENT PHONE` → `agent phone`). It then picks the fields it needs (NAME, PHONE, PRODUCT NAME, AMOUNT, ADDRESS, CITY, AGENT PHONE) and sends the SMS.

So **AGENT PHONE** is taken from whichever column has that header, not from a fixed column letter.

## Adjusting the range

- If your headers and data start in **A** and end in **V**, use `$A$1:$V$1` and `A2:V2` (and A3:V3 in row 3, etc.).
- Make sure the range **includes the column whose header is "AGENT PHONE"** and that row 1 really contains that header text.

## Required headers in row 1

The server looks for these (any casing, spaces normalized):

- **NAME**, **PHONE** or **ALT NO** (at least one), **PRODUCT NAME**, **AMOUNT**, **ADDRESS**, **CITY**, **AGENT PHONE**

Your first row must contain these exact header names in the columns that hold the corresponding data.
