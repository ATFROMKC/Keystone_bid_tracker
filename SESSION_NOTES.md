# SESSION_NOTES.md

Use concise entries. Keep only high-signal notes that help the next session start fast.

## Entry Template

### YYYY-MM-DD - Short session title

- Objective:
- Files changed:
- Commit hash: (or `n/a`)
- Follow-ups:

---

### 2026-02-26 - Context system bootstrap

- Objective: Add persistent context bootstrap docs and an always-on Cursor rule.
- Files changed: `AGENTS.md`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`, `NEXT_CHAT_CHECKLIST.md`, `.cursor/rules/context-first.mdc`, `HANDOFF.md`
- Commit hash: `n/a`
- Follow-ups:
  - Use `NEXT_CHAT_CHECKLIST.md` at the start of new chats.
  - Append one new entry at the end of each coding session.

---

### 2026-02-26 - Phase 1 database foundation

- Objective: Implement Commercial Notebook Phase 1 in the database layer only.
- Files changed: `keystone_bid_tracker/database.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Phase 2 will add `est_complete_date` editing in the PM Edit Job flow (not `mark_won_dialog.py`).
  - Validate new `get_pm_*` methods against real PM tab/report consumers during Phase 2/3 wiring.

---

### 2026-02-26 - PM edit job est complete date

- Objective: Add PM right-click Edit Job support for editable `est_complete_date` and persist manual override with `est_complete_date_manual=1`, while keeping `mark_won_dialog.py` unchanged.
- Files changed: `keystone_bid_tracker/ui/awarded_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Verify right-click `Edit Job` UX in PM Job Manager and confirm manual date saves correctly.
  - Confirm Moraware sync still respects manual override (`est_complete_date_manual=1`).

---

### 2026-02-26 - PM edit job crash fix

- Objective: Debug and fix PM Jobs right-click `Edit Job` crash caused by missing `QDate` import in `awarded_tab.py`.
- Files changed: `keystone_bid_tracker/ui/awarded_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Re-verify right-click `Edit Job` in-app on a normal PM row.
  - If needed, capture terminal traceback for any remaining edge-case crashes.

---

### 2026-02-26 - Phase 2 PM job manager expansion

- Objective: Complete remaining Phase 2 PM Job Manager work: job type/est complete columns, pending row coloring, job type filter, expanded context menu, and PM export.
- Files changed: `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/utils/excel_export.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Run in-app validation for new PM grid/filter/context menu/export flows.
  - Confirm Open in Moraware launches correctly for linked jobs and shows guardrails for unlinked jobs.

---

### 2026-02-26 - PM status logic alignment

- Objective: Separate PM notebook pending logic from invoice status logic, restore notebook-only row tinting, and normalize invoice complete detection.
- Files changed: `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/database.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Verify pending row tint reflects not-started jobs only (template-date based).
  - Spot-check invoice badge transitions for Pending/Partial/Invoiced on mixed-status jobs.

---

### 2026-02-26 - Stop-point docs update

- Objective: Document current PM Job Manager state and capture the new direction to remove row coloring and move to stage-based filtering.
- Files changed: `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Implement stage-focused PM filter model for not-started vs started progression and remove `Year` filter to reduce crowding.
  - Re-test status presentation after the filter redesign is in place.

---

### 2026-02-26 - Moraware URL + job number persistence

- Objective: Fix PM right-click `Open in Moraware` URL construction and persist/display friendly Moraware Job Number across PM linking and Job Manager grid.
- Files changed: `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Verify in-app that `Open in Moraware` opens the correct job from PM right-click menu.
  - Spot-check existing linked records where `moraware_job_number` may still be empty until re-link/resync.

---

### 2026-02-26 - Moraware job # backfill + detail panel

- Objective: Backfill missing Moraware Job # values for already-linked PM jobs during sync and display Moraware Job # in the bottom-left Job Manager detail panel.
- Files changed: `keystone_bid_tracker/utils/moraware_client.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/database.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Run a full PM sync pass and confirm previously blank `MW Job #` cells are populated where Moraware exposes a job number.
  - Spot-check a few rows with still-blank values to confirm whether Moraware source data is missing or labeled differently.

---

### 2026-02-26 - Combined invoice phase reconciliation

- Objective: Reconcile combined Moraware invoice activities (e.g., `ST1, ST2`) to canonical Job Ticket A phase rows, avoid phantom combined phase rows, and prevent non-invoice activities from reverting completed phase status.
- Files changed: `keystone_bid_tracker/utils/moraware_client.py`, `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Re-sync job `17163` and verify both `ST1` and `ST2` remain `Complete` with no `ST1, ST2` synthetic row.
  - Spot-check one mixed-pattern job (combined + standalone invoice activities) and one single-phase job for regression.

---

### 2026-02-26 - PM stage filter and year removal

- Objective: Simplify PM Job Manager filtering by removing the `Year` filter and introducing stage-focused filtering (`Not Started`, `In Progress`, `Complete`) as the primary workflow.
- Files changed: `keystone_bid_tracker/ui/awarded_tab.py`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Validate stage filter behavior on representative jobs for each stage bucket.
  - Fine-tune stage filter labels/tooltips if users want different naming.

---

### 2026-02-26 - Phase 3 PM overview vertical slice

- Objective: Begin Phase 3 by adding a new PM Overview tab with Current Month Dollars and Current Month Square Feet panels wired to existing overview stats.
- Files changed: `keystone_bid_tracker/ui/pm_overview_tab.py`, `keystone_bid_tracker/ui/main_window.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Add the remaining four Phase 3 overview panels.
  - Add visual emphasis to the Current Month Square Feet panel per spec.

---

### 2026-02-26 - Pipeline forecast pivot + month tracking

- Objective: Pivot Phase 3 from generic Overview to Pipeline forecasting, add month-level start tracking for not-started jobs, and surface backlog/90-day/history views in PM.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_overview_tab.py`, `keystone_bid_tracker/ui/main_window.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Normalize Moraware created-date parsing to ISO (`yyyy-mm-dd`) before storage if cross-screen date math is needed.
  - Add a dedicated PM report tab (`ui/pm_reports_tab.py`) and compare forecast vs actual by month.

---

### 2026-02-26 - Rolling 90-day pipeline refinement

- Objective: Refine the Pipeline tab from fixed month slicing to a true rolling 90-day window and add an unscheduled-not-started action queue.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_overview_tab.py`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Decide whether 90-day forecast should also expose row counts alongside dollars per bucket.
  - Add direct "Edit Job" jump from unscheduled queue rows for faster scheduling.

---

### 2026-02-26 - Session notes follow-up entry

- Objective: Record completion of the rolling 90-day pipeline refinement pass and confirm notes are up to date.
- Files changed: `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Re-open PM Pipeline tab in-app and spot-check unscheduled queue rows against Job Manager data.

---

### 2026-02-26 - Pipeline data and UI reset

- Objective: Rework PM Pipeline to use Moraware-synced invoice data only (no bid totals), split clutter into `Pipeline Forecast` and `Completed History` tabs, and add a separate Needs Sync queue excluded from forecast totals.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_overview_tab.py`, `keystone_bid_tracker/ui/pm_history_tab.py`, `keystone_bid_tracker/ui/main_window.py`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Validate a few known jobs where invoice_data is sparse to confirm expected near-zero forecast values.
  - Optionally add row-click action from Needs Sync table to open/link jobs from Job Manager workflows.

---

### 2026-02-26 - Unscheduled semantics and 90+ bucket fix

- Objective: Correct Pipeline semantics so jobs with no Moraware template date remain in the Unscheduled list even after estimated start is set, remove est-complete dependency from Pipeline forecasting, add a 90+ aggregate, and add right-click Edit Job on Unscheduled rows.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_overview_tab.py`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Verify one unscheduled job with estimated month still appears in Unscheduled and also contributes to rolling/90+ forecast as expected.
  - Consider adding row-count KPIs beside dollar/SF totals for easier PM scanability.

---

### 2026-03-01 - Folder move cleanup and note-prompt rule

- Objective: Clean up repo-root local artifacts after moving project folders and update persistent guidance to require explicit user confirmation before appending `SESSION_NOTES.md` entries.
- Files changed: `AGENTS.md`, `.cursor/rules/context-first.mdc`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - If desired, commit doc/rule updates separately from PM feature code changes for cleaner history.

---

### 2026-03-02 - Account report won-customer status fix

- Objective: Fix Account Bid Report logic so bids marked `WON` only appear as awarded for the account in `won_customer_id`; show as `BIDDING` for other linked accounts.
- Files changed: `keystone_bid_tracker/database.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Re-run the Highland Millshop account report and confirm Gilmore Bell shows `BIDDING` instead of `AWARDED`.
  - Spot-check one account that actually won a shared bid to confirm it still shows `AWARDED`.

---

### 2026-03-02 - Estimator open bid folder parity

- Objective: Add `Open Bid Folder` in Estimator Portal Bids for both right-click row actions and detail panel actions, using PM-style Dropbox year/month folder resolution.
- Files changed: `keystone_bid_tracker/ui/bid_detail.py`, `keystone_bid_tracker/ui/bids_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In Estimator Portal, verify `Open Bid Folder` works from both context menu and detail panel for a known bid.
  - Validate warning behavior for missing Dropbox path, invalid bid date, and missing year/month folder.

---

### 2026-03-02 - PM Moraware-driven tab MVP

- Objective: Replace PM Job Manager flow with MVP tab split (`Active Jobs`, `Pending Award`, `Completed History`) where Active Jobs is Moraware-driven with local link overlay and Pending Award is won-unlinked local bids.
- Files changed: `keystone_bid_tracker/ui/main_window.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/pm_pending_award_tab.py`, `keystone_bid_tracker/database.py`, `keystone_bid_tracker/utils/moraware_client.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Run in-app PM validation: auto-load Active Jobs on open, PM hybrid filter behavior, manual refresh behavior, and mismatch flaging for linked non-`WON` bids.
  - Verify Pending Award parity for edit/move-back/open-folder workflows and confirm Completed History remains unchanged.
  - Keep sync-dialog de-duplication as a separate follow-up pass (non-blocking for MVP).

---

### 2026-03-02 - Active Jobs regression stabilization

- Objective: Fix Active Jobs regressions by correcting PM-filter/count behavior, restoring detail panel and PM actions, and using PM-session caching to prevent laggy tab switching.
- Files changed: `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/main_window.py`, `keystone_bid_tracker/utils/moraware_client.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Validate PM-specific count parity (e.g., Evan) against Moraware UI after normalization and active-status filtering updates.
  - In PM portal, verify linked-row detail panel + sync actions and confirm no network refetch occurs on tab switch unless manual refresh is triggered.

---

### 2026-03-02 - Active Jobs Moraware status parity

- Objective: Align PM Active Jobs source counts to Moraware's `Evan Active Jobs` semantics and replace local started/not-started stage logic with Moraware-native status filtering.
- Files changed: `keystone_bid_tracker/utils/moraware_client.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In PM Active Jobs, verify `Moraware Status` buckets (`Active`, `Unscheduled`, `30+ Days Old`) each return expected rows for Evan.
  - Spot-check count parity against the same-day Moraware saved view after a manual Refresh.

---

### 2026-03-02 - Active Jobs right-click link to local bid

- Objective: Add PM Active Jobs right-click linking so users can link a Moraware job to any local bid, with non-blocking warnings for existing links and immediate grid refresh.
- Files changed: `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/link_local_bid_dialog.py`, `keystone_bid_tracker/database.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In PM Active Jobs, verify `Link to Local Bid...` flow on both linked and unlinked rows and confirm warning/continue behavior matches expectations.
  - Revisit true many-to-many bid/job linking design before removing current warning-based guardrails.

---

### 2026-03-02 - Active Jobs link autofill for PM and salesperson

- Objective: Ensure linking a Moraware job from Active Jobs always overwrites local bid `salesperson` and `project_manager` with Moraware values so the bottom-left detail panel reflects linked job ownership immediately.
- Files changed: `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/database.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Re-link a known row (e.g., `Ft Riley CDC`) and confirm detail panel now shows Moraware `Salesperson` and `Project Manager`.
  - Decide later whether manual overrides of these fields should be preserved or always replaced on every link.

---

### 2026-03-02 - Split Date Won from Moraware date

- Objective: Separate local `Date Won` tracking from Moraware-created-date tracking by introducing `won_date` and updating won edit/display flows to stop using `moraware_job_date` as a proxy.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/mark_won_dialog.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/ui/pm_pending_award_tab.py`, `keystone_bid_tracker/ui/bids_tab.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/pm_overview_tab.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app check: Mark Won defaults `Date Won` to today and persists to PM `Date Won` fields without changing `Moraware Date`.
  - Run a quick DB sanity check on older WON rows to confirm linked blank `won_date` rows were backfilled from `moraware_created_date` and unlinked WON rows remain blank.

---

### 2026-03-02 - PM refresh job metadata backfill

- Objective: Expand PM Active Jobs refresh actions so linked-job refresh updates local metadata fields used in the bottom-left detail panel, with `won_date` backfilled from Moraware created date only when blank.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In PM Active Jobs, run `Refresh Selected Job` on a linked row with blank Salesperson/PM/Moraware Date and verify detail panel repopulates.
  - Confirm existing non-blank `Date Won` values remain unchanged after `Refresh Selected Job` and `Refresh All Jobs`.

---

### 2026-03-02 - Date won clamp + refresh UX declutter

- Objective: Enforce `won_date` reconciliation so it never remains later than `moraware_created_date` across all relevant write paths, and reduce PM Active Jobs refresh clutter by removing top selected refresh and clarifying list reload labeling.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In PM Active Jobs, verify top bar now shows `Reload Job List` + `Refresh All Jobs` and selected-job refresh is only in panel/context actions.
  - Spot-check a linked row where `Date Won` > `Moraware Date` and confirm refresh clamps `Date Won` down to `Moraware Date`.

---

### 2026-03-02 - Docs alignment with current architecture

- Objective: Reconcile core markdown docs with the actual current codebase state (PM tab architecture, refresh semantics, and won-date/Moraware-date rules) to remove stale contradictions.
- Files changed: `PROJECT_CONTEXT.md`, `HANDOFF.md`, `KEYSTONE_BID_TRACKER_SPEC.md`, `moraware_scraping_cheatsheet.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Spot-check any future PM architecture changes against `PROJECT_CONTEXT.md` in the same session they land.
  - Consider splitting `KEYSTONE_BID_TRACKER_SPEC.md` into `CURRENT_ARCHITECTURE.md` and `LEGACY_SPEC.md` if the mixed historical/current structure becomes noisy.

---

### 2026-03-02 - Docs alignment closeout note

- Objective: Confirm docs-alignment pass is complete and session notes are up to date after validation.
- Files changed: `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - If PM workflow changes again, update `PROJECT_CONTEXT.md` in the same PR/session to prevent drift.

---

### 2026-03-03 - App icon rollout

- Objective: Roll out the new BidTracker icon by extracting canonical SVG sources, generating production PNG/ICO assets, wiring runtime app icon loading, and documenting Windows build icon usage.
- Files changed: `keystone_bid_tracker/Assets/bidtracker-icon.html`, `keystone_bid_tracker/Assets/icons/bidtracker-full.svg`, `keystone_bid_tracker/Assets/icons/bidtracker-small.svg`, `keystone_bid_tracker/Assets/icons/bidtracker-16.png`, `keystone_bid_tracker/Assets/icons/bidtracker-24.png`, `keystone_bid_tracker/Assets/icons/bidtracker-32.png`, `keystone_bid_tracker/Assets/icons/bidtracker-48.png`, `keystone_bid_tracker/Assets/icons/bidtracker-64.png`, `keystone_bid_tracker/Assets/icons/bidtracker-128.png`, `keystone_bid_tracker/Assets/icons/bidtracker-256.png`, `keystone_bid_tracker/Assets/icons/bidtracker-512.png`, `keystone_bid_tracker/Assets/icons/bidtracker.ico`, `keystone_bid_tracker/main.py`, `keystone_bid_tracker/docs/BUILD_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Run in-app visual validation for titlebar/taskbar icon legibility at small sizes on the target Windows machine.
  - Ensure packaging command/script uses `--icon "keystone_bid_tracker/Assets/icons/bidtracker.ico"` for release builds.

---

### 2026-03-03 - Moraware fast sync client groundwork

- Objective: Implement the fast-sync migration groundwork in `moraware_client.py` by adding API-first bulk sync methods behind `use_fast_sync=True` while preserving all legacy per-job methods and fallback behavior.
- Files changed: `keystone_bid_tracker/utils/moraware_client.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Rewire `InvoiceSyncWorker` in `keystone_bid_tracker/ui/awarded_tab.py` to call `sync_invoice_data_fast(...)` and keep a legacy toggle path.
  - Add optional batch metadata DB update helper in `keystone_bid_tracker/database.py` after UI wiring if throughput needs it.

---

### 2026-03-03 - Fast sync wiring + parity validation

- Objective: Complete Moraware fast-sync migration by wiring `InvoiceSyncWorker` in `awarded_tab.py` to bulk sync, hardening API/fallback behavior in `moraware_client.py`, and validating output parity against legacy sync on known linked jobs.
- Files changed: `keystone_bid_tracker/utils/moraware_client.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/diagnostics/compare_fast_sync_parity.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Optional: keep refining tenant-specific API include/filter shape to reduce `fallback_hits` while preserving parity guarantees.
  - Run in-app PM sync smoke test in Awarded tab (`Sync Invoices from Moraware` and single-job `Refresh`) to confirm UX timing and status updates feel correct.

---

### 2026-03-04 - Multi-link Moraware implementation

- Objective: Implement hybrid primary-link many-to-many Moraware linking with aggregate-all invoice sync behavior, while preserving legacy `bids.moraware_job_id` compatibility and validating parity/sync stability.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/awarded_tab.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Add explicit UI surface in bid detail screens to list/manage all linked Moraware jobs (primary + secondary) instead of relying only on dialog/PM flows.
  - Consider introducing source-job-aware invoice grouping in the detail panel if same phase names across linked jobs cause readability issues for PM users.

---

### 2026-03-04 - Multi-job split allocation workflow

- Objective: Implement split allocation across multiple linked Moraware jobs with strict sum validation and switch PM totals/forecast rollups to use allocation rows as source-of-truth (with safe fallback).
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/split_moraware_allocation_dialog.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Add a dedicated linked-jobs + allocation entrypoint in bid detail panels so users can open allocation editor without going through linking actions.
  - If desired, add automatic proportional prefill helpers (e.g., by reference TP/SF) while keeping strict validation before save.

---

### 2026-03-03 - Minimal-UI parent/child split bids

- Objective: Implement the minimal-UI parent/child split model with manual split action only, Moraware-data prefill for allocations, parent exclusion from rollups, and parent-hidden default lists to prevent double counting.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/split_moraware_allocation_dialog.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Run in-app split smoke test on one multi-link WON bid to verify child creation, parent hiding, and rollup totals.
  - Decide whether to add an unsplit/remerge admin path or keep split as one-way for now.

---

### 2026-03-03 - Live Moraware split prefill + link-state clarity

- Objective: Improve split allocation workflow for newly linked unsynced jobs by adding live Moraware TP/SF prefill, while reducing Primary confusion and making PM Active Jobs link state reflect secondary links.
- Files changed: `keystone_bid_tracker/utils/moraware_client.py`, `keystone_bid_tracker/ui/split_moraware_allocation_dialog.py`, `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app validate a known pair (e.g., `19716` + `19717`) using `Use Live Moraware Data`, confirming non-zero refs appear pre-sync where Moraware has invoice/activity data.
  - Confirm PM Active Jobs rows no longer show false `Not Linked` when a job is linked as secondary.

---

### 2026-03-03 - Linking + unsync workflow alignment

- Objective: Implement PM/Bid linking workflow alignment by adding PM Unsync, enforcing link->WON customer selection for pending bids, supporting multi-job link selection in Bid portal, and adding PM quick add-another-job flow.
- Files changed: `keystone_bid_tracker/database.py`, `keystone_bid_tracker/ui/pm_active_jobs_tab.py`, `keystone_bid_tracker/ui/manual_sync_dialog.py`, `keystone_bid_tracker/ui/moraware_sync_dialog.py`, `keystone_bid_tracker/ui/bids_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify PM `Unsync from Moraware` removes links/invoice rows while preserving bid status.
  - Validate bid-side multi-select link flow and pending->won customer prompt behavior on a real project.

---

### 2026-03-05 - Add Bid multi-account selection fix

- Objective: Fix initial `Add New Bid` account picking so users can reliably select multiple accounts during first entry.
- Files changed: `keystone_bid_tracker/ui/add_bid_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify the Add Bid dialog can save with 2+ selected accounts and shows all selected names in the Bids table.
  - Reopen an edited bid and confirm previously selected accounts remain checked in the dialog.

---

### 2026-03-05 - Bids header filtered stats update

- Objective: Remove the `ACTIVE` stat card from the Bids header and make remaining stat cards reflect the currently filtered bid table rows.
- Files changed: `keystone_bid_tracker/ui/bids_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify that changing Year/Estimator/Status/Search updates `TOTAL BIDS`, `WON`, and `TOTAL VALUE` immediately.
  - Confirm `Showing X bids` aligns with table row count and no longer shows a global total denominator.

---

### 2026-03-05 - Bids won metrics cards

- Objective: Add `Total Won Value` and count-based `Win %` cards to the Bids header, with card order aligned to workflow (`Total Bids`, `Total Value`, `Won`, `Total Won Value`, `Win %`) and all values based on current filters.
- Files changed: `keystone_bid_tracker/ui/bids_tab.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify `Win %` updates correctly for edge cases (no rows = `0.0%`, WON-only filter with rows = `100.0%`).
  - Confirm `Total Won Value` tracks only filtered `WON` rows and remains aligned with active table filters.

---

### 2026-03-05 - Portal state + Bids responsive/detail UX polish

- Objective: Improve cross-portal window consistency by preserving normal/maximized state on Hub/Estimator/PM switches, make Bids header cards/logo responsive across widths, and add a temporary `Hide` control for the bottom bid detail panel that auto-reopens on next row click.
- Files changed: `keystone_bid_tracker/main.py`, `keystone_bid_tracker/ui/bids_tab.py`, `keystone_bid_tracker/ui/bid_detail.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app validate portal switching in both normal and maximized states for Hub -> Estimator -> PM -> Hub sequences.
  - Resize Estimator Bids window across narrow/medium/maximized widths and confirm card spacing + logo scale remain visually balanced.
  - Verify detail panel `✕` hide action collapses panel and that clicking another bid row reopens with correct data.

---

### 2026-03-05 - Bid detail header close-control alignment

- Objective: Refine bid detail panel header UX by removing duplicate top `Add Revision` action and keeping a right-aligned top `✕` close control with better visual alignment.
- Files changed: `keystone_bid_tracker/ui/bid_detail.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify only one `Add Revision` action remains (bottom action bar).
  - Confirm top-right `✕` aligns with the Revision History header row and still hides the detail panel correctly.

---

### 2026-03-06 - Add Bid estimator autocomplete dropdown

- Objective: Improve Add/Edit Bid entry UX by changing `Estimator` to an editable dropdown populated from historical estimator names while still allowing new typed values.
- Files changed: `keystone_bid_tracker/ui/add_bid_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify Add Bid shows historical estimator options and accepts a new typed estimator not already in the list.
  - Confirm Edit Bid preselects the estimator when available and preserves existing estimator text when not present in current options.

---

### 2026-03-06 - PM link review visual refinement

- Objective: Refine `Review Bid/Job Link` readability with bordered left/right info cards, subtle section dividers, improved label/value hierarchy, and gentle delta highlighting while preserving existing linking behavior.
- Files changed: `keystone_bid_tracker/ui/link_review_dialog.py`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - In-app verify bid and Moraware sections remain visually balanced at typical dialog sizes.
  - Confirm delta color treatment feels informative (not noisy) across near-match and mismatch examples.

---

### 2026-03-06 - Root cleanup before GitHub sharing

- Objective: Reduce root-folder clutter before sharing by archiving generated build outputs, moving retained release helpers into `tools/release`, and expanding `.gitignore` to keep generated artifacts out of source control.
- Files changed: `.gitignore`, `tools/release/build_windows_exe.bat`, `tools/release/Keystone Bid Tracker.spec`, `_archive/build-outputs-2026-03-06/`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Confirm no additional generated artifacts should be archived before publishing a review branch.
  - Create/push a dedicated review branch and share the branch URL with read-only access.

---

### 2026-03-06 - Share-ready branch + packaged exe handoff prep

- Objective: Publish a reviewer branch snapshot, complete safe root reorganization moves (`docs/` + `reference/`), and generate a zipped Windows test build for non-technical one-click testing.
- Files changed: `docs/`, `reference/`, `tools/release/`, `_archive/`, `packages/Keystone_Bid_Tracker_Windows_Test_Build.zip`, `SESSION_NOTES.md`
- Commit hash: `a727dfa` (root move-only reorg on `review/share-for-readonly`; branch pushed)
- Follow-ups:
  - Remind testers to fully extract the zip and run from a writable folder so `config.json` can persist local settings.
  - Include tester note that PM `Pending Award` and `Completed History` remain unfinished/in-progress.

---

### 2026-03-05 - Add reviewer-facing README and setup guide

- Objective: Create share-friendly documentation so reviewers/testers can understand project status, local config requirements, and startup/setup steps.
- Files changed: `README.md`, `docs/SETUP.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - Commit and push docs updates so they appear on GitHub.
  - Verify rendered markdown on GitHub (`README.md` and `docs/SETUP.md`) after push.

---

### 2026-03-05 - Docs push confirmation for reviewer branch

- Objective: Finalize and publish reviewer documentation updates to remote branch for GitHub sharing.
- Files changed: `README.md`, `docs/SETUP.md`, `SESSION_NOTES.md`
- Commit hash: `c474128` (`review/share-for-readonly`)
- Follow-ups:
  - Open PR and verify markdown rendering on GitHub before sharing with external reviewers.

---

### 2026-03-17 - Archive legacy Keystone Bid Tracker folder

- Objective: Record decision to move the old `Keystone Bid Tracker` (Node/web prototype) tree out of the active workspace into an `Archive Projects` folder; current app remains `Keystone Bid Tracker 2` (PyQt) only.
- Files changed: `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - If anything still pointed at the old path, update shortcuts or scripts; normal launch is `keystone_bid_tracker/main.py` or packaged exe under Bid Tracker 2.

---

### 2026-03-17 - Two-machine Cursor workflow (commit + push)

- Objective: Keep `review/share-for-readonly` in sync between computers via GitHub (`origin` = `https://github.com/ATFROMKC/Keystone_bid_tracker.git`).
- Workflow (end of session): `git status` → `git add` → `git commit -m "..."` → `git push` on the active branch.
- Workflow (start on other machine): `git pull` before editing; resolve conflicts if any, then continue.
- Files changed: `SESSION_NOTES.md`, `.gitignore` (ignore `packages/*.zip` so test build zips stay local and out of the repo)
- Commit hash: `n/a`
- Follow-ups:
  - On the second PC, clone or fetch the same repo and check out `review/share-for-readonly` (or merge to `main` when ready).
  - Never commit `keystone_bid_tracker/config.json` (already gitignored).

---

### 2026-03-17 - Cursor rule: git session sync + SESSION_NOTES

- Objective: Add an always-on Cursor rule so each session starts with a **`git pull`** reminder and session end runs **status → stage → commit (user or AI message) → push → append `SESSION_NOTES.md`**; align `AGENTS.md`, `context-first.mdc`, and `NEXT_CHAT_CHECKLIST.md`. Note: true “on editor close” automation is not possible—user must wrap up with the agent or ask to sync.
- Files changed: `.cursor/rules/git-session-sync.mdc` (new), `.gitignore` (track `.cursor/rules/**`; ignore rest of `.cursor/`), `AGENTS.md`, `.cursor/rules/context-first.mdc`, `NEXT_CHAT_CHECKLIST.md`, `SESSION_NOTES.md`
- Commit hash: `n/a`
- Follow-ups:
  - At end of future sessions, say “wrap up” / “sync” / “push” so the agent runs the full close sequence.

---

### 2026-03-23 - Merge `review/share-for-readonly` into `main`

- Objective: Bring Cursor rules, git-session-sync docs, and related session notes onto **`main`** so day-to-day work and the other PC can use **`main`** only.
- Actions: `git checkout main` → `git pull origin main` → `git merge origin/review/share-for-readonly` → `git push origin main`.
- Files changed: merge brought in `.cursor/rules/*.mdc`, `AGENTS.md`, `NEXT_CHAT_CHECKLIST.md`, `.gitignore`, `SESSION_NOTES.md` updates from the review branch.
- Commit hash: `526c80a` (merge commit on `main`)
- Follow-ups:
  - On the new PC: `git checkout main` → `git pull` to get the same state.
  - Continue using **`main`** for daily work; keep or delete `review/share-for-readonly` as preferred.

---

### 2026-03-23 - Windows launcher, taskbar icon, gitignore .venv

- Objective: Console-free launch via `launch_keystone_bid_tracker.cmd`, Desktop shortcut script with `bidtracker.ico`, Windows taskbar/pin behavior via `SetCurrentProcessExplicitAppUserModelID`, document multi-PC workflow; ignore `.venv/` in Git.
- Files changed: `.gitignore`, `README.md`, `keystone_bid_tracker/main.py`, `launch_keystone_bid_tracker.cmd`, `scripts/create_desktop_shortcut.ps1`, `SESSION_NOTES.md`
- Commit hash: `f41a467`
- Follow-ups:
  - Other PC: `git pull` on `main`, create `.venv` once, `pip install -r requirements.txt`, re-run `scripts\create_desktop_shortcut.ps1` if you want a fresh Desktop shortcut.

---

### 2026-03-23 - Launcher: `start` + `launch_app.py` (cwd + error log)

- Objective: Double-clicking `launch_keystone_bid_tracker.cmd` does not leave a Command Prompt open (`start ""` detaches `pythonw` / `pyw`). Entry **`scripts/launch_app.py`** sets repo root as cwd and writes Python tracebacks to **`%TEMP%\KeystoneBidTracker_last_error.txt`** (`pythonw` hides stderr).
- Files changed: `launch_keystone_bid_tracker.cmd`, `scripts/launch_app.py`, `README.md`, `SESSION_NOTES.md`
- Commit hash: `cae7fe1`
- Follow-ups:
  - Native/Qt crashes (not Python exceptions) may still exit silently; use `python keystone_bid_tracker/main.py` in a console to debug.

