# PROJECT_CONTEXT.md

## Project Snapshot

- Project: Keystone Bid Tracker
- Type: PyQt5 desktop application
- Entry point: `keystone_bid_tracker/main.py`
- Current app version constant: `1.0.0`

## Current vs Historical Docs

- Source of truth order:
  1. code in `keystone_bid_tracker/`
  2. `PROJECT_CONTEXT.md`
  3. `SESSION_NOTES.md`
  4. historical docs (`HANDOFF.md`, old specs/notes)
- Use `HANDOFF.md` as archive context only, not present-state architecture.

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

- The PM portal currently has three tabs:
  - **Active Jobs** (`ui/pm_active_jobs_tab.py` — `PMActiveJobsTab`)
  - **Pending Award** (`ui/pm_pending_award_tab.py` — `PMPendingAwardTab`)
  - **Completed History** (`ui/pm_history_tab.py` — `PMHistoryTab`)
- PM tab wiring lives in `ui/main_window.py`.
- `ui/awarded_tab.py` is still important, but now mostly provides shared PM components:
  - `AwardedDetailPanel`
  - `InvoiceSyncWorker`
  - `PMEditJobDialog`

## Active Build: Commercial Notebook PM Features

The PM build moved from a single Job Manager view to a split workflow:

1. **Active Jobs** (Moraware-driven list with local bid link overlay)
2. **Pending Award** (local WON bids not yet linked to Moraware)
3. **Completed History** (monthly invoice-complete rollups)

Current PM refresh semantics:

- `Reload Job List` = refresh Moraware list in `Active Jobs` only (no local metadata writes)
- `Refresh Job` / `Refresh All Jobs` = refresh linked local bid metadata + invoice data

### Key data logic rules (read before prompting on any phase):

Some rules below describe pipeline/notebook logic that still exists in code but is not
the primary PM portal entry flow (which is now Active Jobs / Pending Award / Completed History).

- **Job Type** is DERIVED, not stored. Check `invoice_data.phase` names:
  phases starting with 'SS' = Solid Surface, 'ST' = Stone. Both = Mixed.
  Fallback: check `solid_surf_sf` vs `stone_sf` on latest `bid_revision`.

- **PM Active Jobs status** is Moraware-driven:
  rows are pulled from Moraware status buckets (`Active`, `Unscheduled`, `30+ Days Old`).

- **Pending Award** is local:
  `status='WON'` and no linked `moraware_job_id`.

- **Legacy stage filters** (`Not Started` / `In Progress` / `Complete`) were part
  of the older PM Job Manager flow and are retained as historical context only.

- **est_complete_date** auto-populates from MAX(`install_date`) across invoice phases
  during every Moraware sync. If `est_complete_date_manual = 1`, sync skips the write.

- **est_start_month** is user-set month-level forecast input (`YYYY-MM-01`) used for
  scheduling estimates on unscheduled jobs (no Moraware template date); assigning it does not
  remove a job from Unscheduled visibility.

- **Complete this month** = phase `invoice_status='Complete'` AND `invoice_date` in
  current month.

- **Pipeline forecasting** uses estimated start (`est_start_month`) for unscheduled jobs and
  actual first template date for active jobs; it does not rely on `est_complete_date`.

- **Combined invoice activities** (e.g., `ST1, ST2`) are reconciled onto the matching
  Job Ticket A phase rows (`ST1`, `ST2`) instead of creating a synthetic combined row.
  Per-phase TP code remains from Job Ticket A unless missing.

- **Invoice status writes**: only actual Invoice activity rows set `invoice_status` /
  `invoice_date`; Template/Install/Contact activity rows do not downgrade completed phases.

- **Complete checks in aggregates/reports** use normalized matching
  (`LOWER(TRIM(COALESCE(invoice_status,''))) = 'complete'`) to avoid case/whitespace drift.

- **Reports tab** shows jobs when they have at least one complete invoice phase with
  `invoice_date` in the selected month. Report Total = SUM of `tp_code` for those phases.
  No manual invoice_date field needed on bids.

- **Moraware created date** is tracked separately in `bids.moraware_created_date`
  when job details are available, instead of overloading `moraware_job_date`.

- **Date Won canonical field** is `bids.won_date`:
  - Backfill rule: if `won_date` is blank and `moraware_created_date` exists, use `moraware_created_date`.
  - Clamp rule: if both exist and `won_date > moraware_created_date`, set `won_date = moraware_created_date`.
  - `moraware_job_date` remains legacy/compatibility only.

- **Rolling forecast window** is computed from `today` through `today + 90 days`
  and includes each overlapping month bucket in the Pipeline tab.

- **90+ view** is a single aggregate bucket beyond the rolling 90-day window.

- **Pipeline forecast math** uses Moraware-linked invoice data rollups (`invoice_data.tp_code`,
  `invoice_data.sq_ft`) and excludes unsynced jobs from totals.

### What is NOT changing during this build:

- Portal architecture (Hub / Estimator / PM switching)
- Database initialization and path behavior
- `AwardedDetailPanel` as the shared PM detail component (still reused from `awarded_tab.py`)
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
- At the end of each coding session, ask exactly: "should I append a concise entry to session_notes.md?"
- If the user says yes, append a new entry to `SESSION_NOTES.md`. If no, do nothing.
