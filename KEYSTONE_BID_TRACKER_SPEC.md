# Keystone Bid Tracker - Complete Build Specification

## Project Overview
A desktop application for Keystone Solid Surfaces to track commercial countertop bids. 
Built in **PyQt5**, compiled to .exe, data stored in a **SQLite database on Dropbox** 
so two users (Austin and his PM) can share access.

---

## Visual Design Target
- Match the aesthetic of the existing **Keystone Description Builder** app
- Dark theme with dark gray/charcoal background (#1e1e1e or similar)
- Clean, modern typography
- Blue accent color for buttons and highlights
- Professional, not flashy — this is a daily work tool
- Consistent padding, subtle borders, well-spaced layout
- Status badges should be color-coded pills (similar to Linear/Notion style)

---

## Tech Stack
- **Language:** Python 3.x
- **UI Framework:** PyQt5
- **Database:** SQLite (single .db file stored on user-configured Dropbox path)
- **Excel Export:** openpyxl
- **Excel Import:** openpyxl (for importing historical backlog)
- **Config:** JSON config file to store the database path (so each user points to same Dropbox file)

---

## Database Schema

### Table: customers
```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### Table: bids
```sql
CREATE TABLE bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bid_name TEXT NOT NULL,
    estimator TEXT NOT NULL,
    original_bid_date TEXT NOT NULL,
    status TEXT DEFAULT 'BIDDING',  -- BIDDING, WON, LOST, DEAD
    won_customer_id INTEGER REFERENCES customers(id),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### Table: bid_customers (GCs on the bid)
```sql
CREATE TABLE bid_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bid_id INTEGER NOT NULL REFERENCES bids(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id)
);
```

### Table: bid_revisions
```sql
CREATE TABLE bid_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bid_id INTEGER NOT NULL REFERENCES bids(id),
    revision_no INTEGER NOT NULL DEFAULT 1,
    revision_date TEXT NOT NULL,
    bid_total REAL DEFAULT 0,
    solid_surf_sf REAL DEFAULT 0,
    stone_sf REAL DEFAULT 0,
    reason TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

## Application Layout

### Window Structure
- Fixed minimum size: 1200x700
- Resizable
- Title: "Keystone Bid Tracker"
- Dark title bar / dark theme throughout

### Tab Structure (Top Navigation)
1. **Bids** (main view, default tab)
2. **Customers**
3. **Reports**
4. **Import**
5. **Settings**

---

## Tab 1: Bids (Main View)

### Summary Stats Bar (top of tab)
Four stat cards in a horizontal row:
- **Total Bids** — count of all bids
- **Active** — count where status = BIDDING
- **Won** — count where status = WON
- **Total Value** — sum of latest revision bid_total across all bids

### Filter/Search Bar (below stats)
- Search box: searches bid_name and customer names (case insensitive)
- Estimator dropdown filter
- Status dropdown filter (All / Bidding / Won / Lost / Dead)
- Year filter dropdown
- "Clear Filters" button
- Shows "Showing X of Y bids" count

### Bid Table
Columns:
| # | Date | Estimator | Bid Name | Customers | Bid Total | Stone SF | Solid SF | Status | Rev |

- **Default sort:** by created_at ascending (oldest first), scrolled to BOTTOM so newest bid is visible
- **Alternating row colors** for readability
- **Color-coded status badges:**
  - BIDDING = blue
  - WON = green
  - LOST = red
  - DEAD = gray
- **Click a row** to expand the bid detail panel below (or inline expand)
- Double-click to open full edit dialog
- Right-click context menu: Edit, Add Revision, Mark Won, Mark Lost, Mark Dead, Delete

### Bid Detail Expand Panel
When a row is clicked, an expand panel slides open below it showing:

**Left column:**
- Full bid name
- Estimator
- Original bid date
- Status badge
- Customers (listed with tags)
- Won By (if WON, shows winning customer)
- Notes

**Right column — Revision History table:**
| Rev # | Date | Bid Total | Stone SF | Solid SF | Reason |
- All revisions listed newest first
- "Add Revision" button at top right of this section

**Action buttons at bottom of panel:**
- Add Revision
- Mark Won (opens dialog to select winning customer)
- Mark Lost
- Mark Dead
- Edit Bid
- Delete Bid (only if status is not WON)

### Add Bid Button
Prominent "+ Add Bid" button in top right of the Bids tab header.

---

## Add Bid Dialog

Modal dialog, dark themed, clean form layout:

**Fields:**
- Bid Name* (text input, large)
- Bid Date* (date picker, defaults to today)
- Estimator* (text input — NOT a dropdown, free text)
- Bid Total* (numeric, $ prefix)
- Solid Surface SF (numeric, optional)
- Stone SF (numeric, optional)
- Customers* (multi-select list with search, at least 1 required)
  - Shows all active customers
  - Search/filter box within customer list
  - "+ Add New Customer" inline button that adds to customer DB and auto-selects
- Notes (multiline text, optional)

**Buttons:** Cancel | Save Bid

**Validation:**
- Bid Name required
- Estimator required
- Bid Total >= 0
- At least one customer selected

---

## Add Revision Dialog

Simpler modal:
- Shows bid name at top (read only)
- Revision # (auto-calculated, read only)
- Revision Date* (date picker, defaults to today)
- New Bid Total*
- Solid Surface SF
- Stone SF
- Reason for revision (text, optional)

**Buttons:** Cancel | Save Revision

---

## Mark Won Dialog

- Shows bid name
- Dropdown: "Select winning customer" (only shows customers on this bid)
- Buttons: Cancel | Confirm Won

---

## Tab 2: Customers

Simple management screen:
- List of all customers (searchable)
- Add New Customer button
- Edit customer name (inline or dialog)
- Toggle active/inactive (inactive customers hidden from bid dropdowns)
- Shows bid count per customer

---

## Tab 3: Reports

Simple reporting view:
- **Date range filter** (from/to)
- **Estimator filter**
- **Status filter**

Report cards/sections:
- Bids by status (count + total value)
- Bids by customer (how many bids, how many won)
- Win rate % overall and by estimator
- Monthly bid volume chart (simple bar chart using PyQt5 or matplotlib)
- Top customers by bid volume

Export Report button — exports current report view to Excel

---

## Tab 4: Import

For importing the historical backlog Excel file.

**UI:**
- File picker to select Excel file
- "Preview Import" button — shows a table of what will be imported
- "Run Import" button — imports all rows
- Progress bar during import
- Summary when done: "X bids imported, X customers created, X skipped (duplicates)"

**Import Mapping from Bid_Tracker_Backlog.xlsx:**
| Excel Column | Maps To |
|---|---|
| BID DATE | original_bid_date, revision_date |
| Estimator | estimator |
| BID NAME | bid_name |
| BID TOTAL $ | bid_total (revision 1) |
| SOLID SURF. SF | solid_surf_sf (revision 1) |
| STONE SF | stone_sf (revision 1) |
| BID TO | customer (create if not exists) |
| BID TO2 | customer (create if not exists) |
| BID TO3 | customer (create if not exists) |
| BID TO4 | customer (create if not exists) |
| Bid Won? | if "Yes" → status = WON |

**Duplicate detection:** skip rows where bid_name + original_bid_date + estimator already exists

**Customer handling:** For each BID TO value, check if customer exists by name (case-insensitive). If not, create it. Link all non-empty BID TO columns to the bid.

---

## Tab 5: Settings

- **Database Path** — text field + browse button to point to the .db file on Dropbox
- "Test Connection" button
- App version info
- "Rebuild Stats" button (recalculates any cached values)

---

## Export to Excel

Available from:
- Right-click menu on bid list
- Reports tab
- A toolbar button "Export All"

Exports to .xlsx with columns matching the original backlog format for compatibility.

---

## Config File

Store a `config.json` next to the .exe:
```json
{
  "database_path": "C:/Users/Austin/Dropbox/Keystone/bid_tracker.db",
  "last_opened": "2026-02-20"
}
```

On first launch with no config, prompt user to set database path.

---

## Key Behaviors

1. **Default scroll position:** Main bid list always scrolls to bottom on load (newest bid visible)
2. **After adding a bid:** Refresh list, scroll to bottom, auto-select/expand the new bid
3. **Customer database:** Builds organically — add inline when adding bids, manage in Customers tab
4. **Revisions:** A bid always has at least 1 revision (created with the bid). The current/latest revision's totals are shown in the main list.
5. **Won bids:** Cannot be deleted. Must be marked a different status first.
6. **Status colors:** Consistent throughout entire app wherever status appears.
7. **Date format:** Display as MM/DD/YYYY throughout UI. Store as ISO in database.
8. **Two users:** Both Austin and PM point their app to same .db file on Dropbox. No user login needed — it's a small team tool.

---

## Files to Create

```
keystone_bid_tracker/
├── main.py                  # Entry point, launches app
├── config.py                # Config file read/write
├── database.py              # All SQLite operations
├── models.py                # Data classes
├── ui/
│   ├── main_window.py       # Main window, tab container
│   ├── bids_tab.py          # Bids main view
│   ├── bid_detail.py        # Expand panel
│   ├── add_bid_dialog.py    # Add bid modal
│   ├── add_revision_dialog.py
│   ├── mark_won_dialog.py
│   ├── customers_tab.py
│   ├── reports_tab.py
│   ├── import_tab.py
│   └── settings_tab.py
├── styles/
│   └── theme.py             # Dark theme QSS stylesheet
└── utils/
    ├── excel_export.py
    └── excel_import.py
```

---

## Style Reference (QSS Dark Theme)

Base the stylesheet on this color palette:
```
Background:       #1a1a1a
Surface/Cards:    #2a2a2a
Border:           #3a3a3a
Text Primary:     #f0f0f0
Text Secondary:   #999999
Accent Blue:      #4a9eff
Accent Hover:     #3a8eef
Success Green:    #4caf50
Error Red:        #f44336
Warning Yellow:   #ff9800
Muted Gray:       #666666
Input Background: #333333
```

Status badge colors:
```
BIDDING:  background #1a3a5c, text #4a9eff
WON:      background #1a3a1a, text #4caf50
LOST:     background #3a1a1a, text #f44336
DEAD:     background #2a2a2a, text #666666
```

---

## Build/Distribution Notes

- Use **PyInstaller** to compile to single .exe
- Include all PyQt5 deps in bundle
- Config file lives next to .exe (not bundled)
- Target: Windows 10/11
