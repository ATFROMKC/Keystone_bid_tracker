# Moraware Scraping Cheat Sheet
**Instance:** keystonesolidsurfaces.moraware.net  
**Version:** v5_0_1115  
**Discovered:** February 2026 via DevTools network analysis

---

## Authentication

**Login URL:** `GET /go`  
**Login POST:** `POST /go`  
**Fields:** `user`, `pwd`, `redirectURL`, `LOGIN`  
**Success indicator:** Post-login URL stays at `/go` with status 200  
**Session:** Cookie-based, maintained via `requests.Session`

---

## Job Page

**URL:** `GET /sys/job/{job_id}`

### Job Details (scraped from main page HTML)

| Field | HTML Location | Notes |
|---|---|---|
| Creation Date | Inline `label: value` text scan | Label normalizes to `created date` or `creation date` |
| Salesperson | Inline `label: value` text scan | Label normalizes to `salesperson` or `sales person` |
| Project Manager | Inline `label: value` text scan | Label normalizes to `project manager` |
| Status | Inline `label: value` text scan | |

**Inline scan pattern:**
```python
for el in soup.find_all(string=True):
    text = el.strip()
    if not text or ":" not in text:
        continue
    if len(text) > 80:
        continue
    if text.count(":") != 1:
        continue
    label, value = text.split(":", 1)
    # normalize label and match against canonical field names
```

### Activities Table

**Selector:** `table` containing `th` headers with "Activity", "Phase", "Status"  
**Rows:** `tbody > tr`  
**Column positions:** Dynamic — detect by scanning `th` text  
**Key columns:** Activity, Phase, Status, Start Date, TP Code (custom, variable position)

**TP Code column detection:**
```python
for i, th in enumerate(header_row.find_all("th")):
    if "tp code" in th.get_text(strip=True).lower():
        tp_col = i
```

**Invoice activity detection:**
```python
if "invoice" in activity_name.lower():
    phase = cells[phase_col].get_text(strip=True)
    tp_code = cells[tp_col].get_text(strip=True) if tp_col else None
```

---

## Forms Section

### Form Title Elements

**Tag:** `<span>` with `onclick="toggleJobFormDisplay(job_id, form_id)"`  
**Class:** `formTitle` (but don't rely on this — use onclick instead)  
**Example:**
```html
<span class="formTitle" onclick="toggleJobFormDisplay(21857,109013)">Job Ticket A</span>
```

**Form ID extraction:**
```python
import re
for span in soup.find_all("span", onclick=True):
    if "job ticket a" in span.get_text(strip=True).lower():
        match = re.search(r"toggleJobFormDisplay\(\d+,(\d+)\)", span["onclick"])
        if match:
            form_id = match.group(1)
```

### Form Container

**Table ID:** `tblJobForm{form_id}`  
**Content cell ID:** `tblJobFormContent{form_id}`  
**`data-delayedLoad` attribute:**  
- `"1"` = collapsed, content not loaded (default on page load)  
- `"0"` = expanded, content present in HTML  

**When collapsed, content loads via AJAX POST (see below).**

---

## AJAX Form Content Endpoint

**URL:** `POST /sys/job/{job_id}?U={timestamp_ms}`  
**Content-Type:** `application/x-www-form-urlencoded`  

**Payload:**
```
C=mjtrs1&X=1&cuid=29&F=Dialog_GetJobFormContentForExpand&P0=[{job_id}]&P1=[{form_id}]
```

**Parameters:**
| Param | Value | Notes |
|---|---|---|
| `C` | `mjtrs1` | Moraware JS constant |
| `X` | `1` | Moraware JS constant |
| `cuid` | `29` | Customer/instance ID — specific to this Moraware account |
| `F` | `Dialog_GetJobFormContentForExpand` | Function name |
| `P0` | `[job_id]` | Job ID in brackets |
| `P1` | `[form_id]` | Form ID in brackets |
| `U` | timestamp ms | Cache-busting, `int(time.time() * 1000)` |

**Triggered by:** `toggleJobFormDisplay(job_id, form_id)` in `JobDetail.js`  
**Initiator chain:** `ClientFunctions.js → RemoteScripting.js → JobDetail.js`

---

## Form Content HTML Structure

**Response contains full form HTML.**  
**Key selector:** `table.formRowTable`

```html
<table class="formRowTable" mjtrownum="6">
  <tr>
    <td mjtrownum="6" mjtcolnum="1">
      <div>TP Code:</div>      <!-- label -->
      <div>19760</div>         <!-- value -->
    </td>
    <td mjtrownum="6" mjtcolnum="2">
      <div>Job Phase Name:</div>
      <div>SS1</div>
    </td>
  </tr>
</table>
```

**Parsing pattern:**
```python
for td in form_soup.select("table.formRowTable td"):
    divs = td.select("div")
    if len(divs) < 2:
        continue
    label = divs[0].get_text(strip=True).replace(":", "").strip().lower()
    value = divs[1].get_text(strip=True)
    if not value or value == "\xa0":
        continue
    if "job phase name" in label:
        phase_name = value
    elif "tp code" in label:
        tp_code = float(value.replace(",", "").replace("$", "").strip())
```

---

## XML API (`/api.aspx`)

**Status: BROKEN for this instance**  
**Error:** `The 'request' element is not declared`  
**Affected calls:** `jobFormsGet`, possibly others  
**Do not use** — fall back to web scraping for all data.

---

## Label Normalization

```python
def _normalize_label(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)  # replace all punctuation with spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text
```

Handles edge cases like:
- `"Project Manager (Primary)"` → `"project manager primary"`
- `"Status - Current"` → `"status current"`
- `"Sales-Person"` → `"sales person"`
- `"Created (UTC)"` → `"created utc"`
- `"TP Code:"` → `"tp code"`

---

## Known Field Values / Examples

| Job | Form ID | Phase | TP Code | Notes |
|---|---|---|---|---|
| 21857 | 109013 | SS1 | 19760 | HCA Lee's Summit Medical Center |

---

## Gotchas

- **Forms are always collapsed on initial page load** — always use the AJAX POST to get form content, never assume `data-delayedLoad="0"`
- **`cuid=29` is instance-specific** — if connecting to a different Moraware account this will be different
- **TP Code column position in activities table is dynamic** — always detect by header text, never hardcode column index
- **XML API is broken** — don't attempt `jobFormsGet` or similar, it will always return a schema validation error
- **Invoice activity TP Code overrides Job Ticket A TP Code** — invoice is source of truth when present
