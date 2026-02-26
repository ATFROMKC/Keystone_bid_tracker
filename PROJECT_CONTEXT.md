# PROJECT_CONTEXT.md

## Project Snapshot

- Project: Keystone Bid Tracker
- Type: PyQt5 desktop application
- Entry point: `keystone_bid_tracker/main.py`
- Current app version constant: `1.0.0`

## Current Architecture

- Three-portal model is active:
  - Hub portal
  - Estimator portal
  - PM portal
- Portal startup and switching are controlled by `PortalController` in `main.py`.
- Last-used portal is persisted through config (`get_last_portal` / `set_last_portal`).

## Data and Environment

- Persistent storage uses SQLite (`Database` in `keystone_bid_tracker/database.py`).
- On first run, user is prompted to select/create a `.db` file (expected in Dropbox).
- Theme is applied at startup via `styles/theme.py`.

## Moraware Integration (Current Known State)

- Integration logic lives in `keystone_bid_tracker/utils/moraware_client.py`.
- Behavior priority for Moraware questions:
  1. `Moraware.JobTrackerAPI5.cs` (authoritative contract)
  2. `CHIP MOREAWARE MD FILES/Moraware_URL_Schema.md` (Keystone-specific mapping)
  3. Current app code in `moraware_client.py`
  4. Supporting notes/docs
- Recent integration work is documented in `HANDOFF.md` (now legacy/archive).

## PM Portal — Current Tab Structure

- The PM portal currently has one tab: **Job Manager** (`ui/awarded_tab.py` — `AwardedTab` class).
- The Job Manager shows all WON bids with invoice tracking, Moraware sync, and a
  detail expansion panel (`AwardedDetailPanel`).
- Two things to never touch during the Commercial Notebook build unless explicitly asked:
  - `InvoiceSyncWorker` and the Moraware invoice sync logic in `awarded_tab.py`
  - `AwardedDetailPanel` — the expandable detail panel below the job list

## Active Build: Commercial Notebook PM Features

The PM portal is being extended to recreate the value of an older internal app called
the "Commercial Project Notebook." The full spec and Cursor prompts live in:

  `Commercial_Notebook_Cursor_Roadmap.docx`

### What is being added (4 phases, do in order):

**Phase 1 — Schema + Auto-Stats** (`database.py` only)
- Add 3 columns to bids table via the existing `new_columns` migration pattern:
  `est_complete_date TEXT`, `est_complete_date_manual INTEGER DEFAULT 0`, `notebook_notes TEXT`
- Add 5 new query methods: `get_pm_notebook_status()`, `get_pm_job_type()`,
  `get_pm_overview_stats()`, `get_pm_monthly_report()`, `get_pm_report_years()`
- Update `upsert_invoice_data()` to auto-write `est_complete_date` from MAX(install_date),
  respecting the manual override flag
- Status: NOT STARTED

**Phase 2 — Job Manager Upgrades** (`awarded_tab.py` only)
- Row color coding: Pending jobs = light salmon, Active jobs = default
- Two new grid columns: Job Type (derived from phase names), Est Complete
- Job Type filter dropdown (client-side filtering)
- Right-click context menu: Edit Job, Open in Moraware, Move Back to Bidding
- Export to Excel button
- Status: NOT STARTED

**Phase 3 — Overview Dashboard Tab** (new file: `ui/pm_overview_tab.py` + `ui/main_window.py`)
- New `PMOverviewTab` class with 6 summary panels:
  1. Current Month Dollar (Complete / Projected / Total by SS and Stone)
  2. Current Month Square Feet — most important panel, highlight visually
  3. Pipeline by Job Type ($)
  4. Pipeline by Job Type (SF)
  5. PM Overview: Current Month
  6. PM Overview: All Active Jobs
- Wire into PMWindow as the first tab (Overview, Job Manager, Reports)
- Status: NOT STARTED

**Phase 4 — Reports Tab** (new file: `ui/pm_reports_tab.py` + `ui/main_window.py`)
- New `PMReportsTab` class
- Month/Year + PM + Job Type filters
- Report Total prominently displayed
- Invoice ledger driven by complete invoice_data phases
- Export to Excel
- Wire into PMWindow as the third tab
- Status: NOT STARTED

### Key data logic rules (read before prompting on any phase):

- **Job Type** is DERIVED, not stored. Check `invoice_data.phase` names:
  phases starting with 'SS' = Solid Surface, 'ST' = Stone. Both = Mixed.
  Fallback: check `solid_surf_sf` vs `stone_sf` on latest `bid_revision`.

- **Active vs Pending** is DERIVED from `invoice_data`:
  Active = at least one phase has a non-null `template_date`.
  Pending = no `template_date` on any phase.

- **est_complete_date** auto-populates from MAX(`install_date`) across invoice phases
  during every Moraware sync. If `est_complete_date_manual = 1`, sync skips the write.

- **Complete this month** = phase `invoice_status='Complete'` AND `invoice_date` in
  current month.

- **Projected this month** = `est_complete_date` in current month AND no complete phase yet.

- **Reports tab** shows jobs when they have at least one complete invoice phase with
  `invoice_date` in the selected month. Report Total = SUM of `tp_code` for those phases.
  No manual invoice_date field needed on bids.

### What is NOT changing during this build:

- Portal architecture (Hub / Estimator / PM switching)
- Database initialization and path behavior
- `InvoiceSyncWorker` in `awarded_tab.py`
- `AwardedDetailPanel`
- `MarkWonDialog` (minor addition of `est_complete_date` field in Phase 1, that's all)
- Moraware source-of-truth order
- Estimator portal, Hub portal, or any Estimator-side tabs

### Parked for a separate future build (do not attempt now):

- Multi-quote / multi-job linking (one quote → multiple Moraware phases, or multiple
  quotes → one job). Requires parent_bid_id relationship design. Separate session.
- Material, Color, Meas type (TEMP/BOD), Method (Install/Pickup/Delivery) fields —
  not needed for any current calculations, add later if needed.

## Known Constraints

- Treat `HANDOFF.md` as historical context, not canonical current state.
- Avoid changing portal architecture unless explicitly requested.
- Avoid changing DB init/path flow unless explicitly requested.
- Keep Moraware protocol assumptions grounded in the truth-order docs above.

## Do Not Change Without Explicit Ask

- Portal structure (Hub/Estimator/PM)
- Database initialization and persisted DB path behavior
- Moraware source-of-truth order
- High-level scope of tabs/workflows unrelated to the active task

## Working Conventions

- Make smallest possible change to satisfy each request.
- Prefer clear docs updates when behavior changes.
- If architecture decisions change, update this file in the same session.
- At the end of each coding session, append a new entry to `SESSION_NOTES.md`.
