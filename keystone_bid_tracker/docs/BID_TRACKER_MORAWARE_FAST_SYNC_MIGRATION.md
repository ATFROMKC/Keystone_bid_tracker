# Bid Tracker Moraware Fast Sync Migration

## Goal
Migrate Bid Tracker Moraware sync from per-job HTML scraping to an EMA-style, API-first fast flow while preserving behavior via fallback paths.

## Current State (Observed)

- Moraware is already integrated and used in:
  - `ui/pm_active_jobs_tab.py` for active job list loading
  - `ui/awarded_tab.py` `InvoiceSyncWorker` for linked-job invoice sync
- Current invoice sync is per-job and network-heavy:
  - `get_invoice_data()`
  - `get_job_status()`
  - `get_job_details()`
- Core client (`utils/moraware_client.py`) is mostly HTML scrape first.

## Migration Scope

### 1) `utils/moraware_client.py`: Add fast path, keep legacy fallback

- Add constants:
  - `_TP_CODE_ACTIVITY_FIELD_ID = "71"`
  - `_JOB_NUMBER_FIELD_ID = "13"`
- Mark these IDs as **Keystone instance-specific** in code comments (same concept as `cuid=29`).
  - Future integrations should re-discover field IDs per Moraware tenant instead of assuming these values.
- Add performance/session setup:
  - mount `HTTPAdapter(pool_connections=25, pool_maxsize=25)` on session
  - use `BeautifulSoup(..., "lxml")` in hot paths
- Add calendar index discovery:
  - `_fetch_calendar_activity_ids(start_date, end_date, activity_type=16)`
- Add batched API methods:
  - `_api_get_job_activities(activity_ids, batch_size=...)`
  - `_api_get_jobs_metadata(job_ids, batch_size=...)`
- Add one bulk sync entrypoint:
  - `sync_invoice_data_fast(linked_jobs, start_date=None, end_date=None, progress_cb=None)`
- Keep legacy methods for residual fallback only:
  - `get_invoice_data`
  - `_get_job_ticket_a_phases`
  - `_get_invoice_activities`
  - `get_job_details`

### 2) `ui/awarded_tab.py`: Rewire `InvoiceSyncWorker` to bulk mode

Current:
- Loop each linked bid and call three client methods per job.

Target:
- Build linked `bid_id <-> moraware_job_id` map once.
- Call one bulk client sync method.
- Upsert rows per bid from grouped result.
- Update `moraware_job_status`, `moraware_job_number`, and sync timestamp from API metadata.
- Keep signal contracts unchanged:
  - `progress(current, total)`
  - `finished(jobs_synced, phases_found)`
  - `error(message)`

### 3) `database.py`: Minimal or no schema changes

Existing fields already support this migration:
- `bids.moraware_job_id`
- `bids.moraware_job_number`
- `bids.moraware_job_status`
- `bids.last_moraware_sync_at`
- `invoice_data` phase/tp/date/status/source

Optional improvement:
- Add helper for batch metadata updates in one transaction for higher throughput.

## Data Mapping Rules (Policy)

- Keystone tenant-specific constants:
  - `_TP_CODE_ACTIVITY_FIELD_ID = "71"` (Activity TP custom field)
  - `_JOB_NUMBER_FIELD_ID = "13"` (Job Number custom field)
  - `cuid = 29` (legacy form AJAX calls)
  - Treat these as non-portable defaults; verify per tenant before rollout.
- TP priority:
  1. Activity TP custom field `id=71`
  2. Job Ticket A fallback by phase
- Job number source:
  - `jobQuery` custom field `id=13`
- Exclude canceled invoice activity rows from synced invoice rows.
- Phase source priority:
  1. `jobPhases/jobPhase/name`
  2. `jobPhase/name`
- If API phase is blank for a fallback candidate:
  - optionally enrich phase from legacy activity table by `jobActivityId` before final fallback decision.
- Keep strict handling:
  - unresolved/ambiguous rows are not silently assigned.

## Recommended Fast Method Contract

Return from bulk sync method:
- `rows_by_job_id: dict[str, list[dict]]`
- `meta_by_job_id: dict[str, dict]`
- `issues: list[dict]` (optional diagnostics)
- `stats: dict` (counts and elapsed timing)

Suggested row shape:
- `phase`
- `tp_code`
- `sq_ft`
- `invoice_date`
- `template_date`
- `install_date`
- `contact_customer_date`
- `contact_customer_notes`
- `invoice_status`
- `source`

## Safe Rollout Sequence

1. Implement fast methods behind feature flag (`use_fast_sync=True`).
2. Wire `InvoiceSyncWorker` to fast path.
3. Keep old per-job path available as fallback toggle.
4. Compare both outputs on the same linked jobs/date range.
5. Promote fast path to default after parity verification.

## Validation Checklist

- Same linked WON bids included.
- Same or explainably stricter phase coverage.
- TP totals stable against accepted baseline.
- `moraware_job_number` populated consistently.
- Runtime significantly improved versus current per-job loop.
- No regressions in:
  - Awarded tab filters/stats/detail panel
  - PM Active Jobs link and refresh actions
  - export flows consuming synced data

## Notes for Implementation Session

- Keep old methods callable for diagnostics and one-off troubleshooting.
- Log batch-level timing and counts (activity IDs found, rows kept, fallback hits).
- Avoid broad `/sys/jobs` scans in the invoice sync hot path.
