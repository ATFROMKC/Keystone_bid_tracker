# HANDOFF.md — Moraware Integration Fixes

## Session Summary

This session implemented 7 fixes to the Moraware integration in the Keystone Bid Tracker PyQt5 app, plus a revert of incorrect earlier edits.

---

## Files Changed

### 1. `keystone_bid_tracker/ui/bids_tab.py`

**Fix 1 — Moraware Sync button moved here from Awarded tab**

- Added `from ui.moraware_sync_dialog import MorewareSyncDialog` import
- Added a "Moraware Sync" button in the header row between "Export All" and "+ Add Bid"
- Added `_on_open_sync_dialog()` method that opens the sync dialog and refreshes on close

### 2. `keystone_bid_tracker/ui/awarded_tab.py`

**Fix 1 — Moraware Sync button removed from here**

- Removed `from ui.moraware_sync_dialog import MorewareSyncDialog` import
- Removed `self.match_btn` ("Match Bids to Moraware") from the header
- Removed `_on_open_sync_dialog()` method
- The Awarded tab still has its own "Sync Invoices from Moraware" button and `InvoiceSyncWorker` — those are untouched

### 3. `keystone_bid_tracker/ui/moraware_sync_dialog.py`

**Fixes 2–6 — Complete rewrite**

- **Fix 2 (Simplified filter):** Replaced two rows of filter combos (status, date range, estimator, customer, PM) with two radio buttons: "Scan unawarded bids only" (default) and "Scan all bids". Removed all associated helper methods (`_get_selected_status`, `_populate_mw_filters`, `_populate_manual_bid_combo`, `_populate_manual_job_combos`, `_filter_manual_jobs`). Rewrote `_get_filtered_bids()` — unawarded mode filters to statuses `BIDDING`, `LOST`, `DEAD`.
- **Fix 3 (Thresholds & grouping):** Minimum threshold raised to 60%. Every bid gets its best match shown. Matches grouped as Strong (85%+, green row), Possible (60–84%, yellow row), No Match (<60%, gray row, no action button). Table reduced from 8 to 7 columns (removed "Alternatives").
- **Fix 4 (ReviewMatchDialog):** New `ReviewMatchDialog` class with side-by-side layout — left panel shows local bid details, right panel shows Moraware job details (fetched via API). Score displayed prominently at top. Buttons: "Confirm Won" / "Not a Match" / "Skip". Each table row has a "Review" button for 60%+ matches. Removed: `_show_alternatives`, `_use_alternative` methods, entire Manual Link section (`QGroupBox`, combos, `_on_manual_link`).
- **Fix 5 (Reuse MarkWonDialog):** Deleted `ConfirmMatchDialog` class entirely. "Confirm Won" opens the existing `MarkWonDialog` with `moraware_job_date`, `salesperson`, and `project_manager` pre-filled from Moraware API data. `FetchJobsWorker.finished` signal changed to `pyqtSignal(list, object)` to emit the authenticated `MorewareClient` for reuse. `_do_link` replaced by `_do_confirm_won`.
- **Fix 6 (QDateEdit crash):** Resolved implicitly — `QDateEdit` is no longer imported or used in this file. The crash-causing code (filter bar date widgets, `ConfirmMatchDialog` date field) was all removed.

### 4. `keystone_bid_tracker/utils/moraware_client.py`

**Fix 7 — XML API replaces scraping for Job Ticket A / invoice data**

**Kept unchanged:** `login()`, `_new_session()`, `_find_login_page()`, `_page_has_login_form()`, `_detect_form_fields()`, `test_login()`, `dump_diagnostics()`.

**Removed (old scraping methods):** `_fetch_job_detail_soup`, `_parse_activities_table`, `_extract_phases`, old `_extract_invoice_activities`, old `_get_job_ticket_a_phases`, `_get_invoice_activities` (convenience wrapper), `_log_page_hints`. `_parse_currency` moved to module-level function.

**Added:**
- `_api_post(request_xml)` — POSTs XML to `{base_url}/api.aspx`, returns parsed `ET.Element`
- `get_job_details(job_id)` — Calls `jobsGet` API, returns `{created_date, salesperson, project_manager, status}`. Used by ReviewMatchDialog to pre-fill MarkWonDialog fields.
- Rewritten `_get_job_ticket_a_phases(job_id)` — Calls `jobFormsGet` API with `includeJobPhases="true" fieldIndicator="AllFields"`. Filters forms where `FormTemplateName` contains "Job Ticket A". Extracts phase from `JobPhases`, TP Code from `FieldValues`.
- `_get_invoice_activities(job_id)` — Still scrapes the activities table (via session GET to `/sys/job/{id}`) for Invoice activities that override Job Ticket A TP Codes.
- `get_invoice_data(job_id)` — Orchestrates: calls `_get_job_ticket_a_phases` then `_get_invoice_activities`, merges with invoice overrides taking priority. Same public signature as before — `InvoiceSyncWorker` in `awarded_tab.py` works unchanged.

### 5. `keystone_bid_tracker/ui/mark_won_dialog.py`

**NOT modified** — used as-is by the new sync flow.

---

## Files NOT Changed

- `main.py`, `config.py`, `database.py`, `models.py` — untouched
- `ui/main_window.py`, `ui/bid_detail.py`, `ui/add_bid_dialog.py`, `ui/add_revision_dialog.py`, `ui/import_tab.py`, `ui/reports_tab.py`, `ui/customers_tab.py`, `ui/settings_tab.py` — untouched
- `utils/excel_export.py`, `utils/excel_import.py` — untouched
- `styles/theme.py` — untouched

---

## Known Considerations

1. **Moraware XML API field names:** The `get_job_details` method tries multiple candidate tag names (e.g. `CreatedDate`, `JobCreatedDate`, `DateCreated`) since the exact Moraware API response schema may vary. If fields come back empty on first real test, enable DEBUG logging on `moraware_client` to see the raw XML and adjust tag names.

2. **Invoice activities still use scraping:** `_get_invoice_activities` fetches the job detail page HTML and parses the `ActivitiesBody` table. This is the only remaining scraping in `moraware_client.py`. The web session from `login()` is reused for this.

3. **`FetchJobsWorker` still scrapes the job list:** The `/sys/jobs` page scraping for building the fuzzy-match candidate list is unchanged. This runs in `moraware_sync_dialog.py` and uses `BeautifulSoup`.
