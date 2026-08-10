# Known gaps (BidTracker today)

**Bottom line:** Several PM/report surfaces are implemented but unwired or partial; Outlook Classic COM is a temporary workaround pending Graph admin consent; and some session docs can lag the code. Treat these as incomplete — do not assume they are production-ready patterns for CounterPro.

Code under `keystone_bid_tracker/` remains authoritative when docs disagree.

---

## Unwired / helper-only UI

| Item | Status |
|---|---|
| `PMOverviewTab` (Pipeline Forecast) | Implemented but **not tabbed** into the PM window in `main_window.py` |
| `AwardedTab` | Unwired as a tab; helpers reused elsewhere (`InvoiceSyncWorker`, `AwardedDetailPanel`, `PMEditJobDialog`) |
| `get_pm_monthly_report` | Database/report helper exists; **no dedicated UI** wired |

---

## Partial PM workflows

- **Pending Award** — local WON bids with no Moraware link; usable but still evolving / incomplete vs desired PM workflow.
- **Completed History** — driven by local `invoice_data` rollups; partial relative to full PM history needs.

See also orientation notes in `handoff/00-orientation/project-overview.md` and `architecture.md`.

---

## Outlook: COM temporary, Graph intended

- Classic Outlook **COM/desktop** sync is a **temporary workaround** while Azure AD admin consent for Microsoft Graph (`Calendars.Read.Shared`) is pending.
- Graph is already implemented in BidTracker and is the **intended** long-term path.
- For CounterPro (hosted on Render), per-machine COM is **not viable** — plan server-side Graph / existing M365; treat COM as functional reference only.

---

## Moraware / sync stubs

- **Dual Moraware ID storage** — `moraware_job_id` and `moraware_job_number` are both stored and must not be conflated (same pitfall CounterPro documents).
- **Calendar activity fast-sync stub** — with `use_fast_sync` (default True), calendar activity id handling can be stubbed/empty in places; scrape fallbacks exist. Do not assume full parity with CounterPro’s Moraware stack; do **not** port the BidTracker client.

---

## Documentation lag

- `OTHER_PC_HANDOFF.md` and `SESSION_NOTES.md` may **lag** current code. Prefer `keystone_bid_tracker/` (then `PROJECT_CONTEXT.md`) when resolving conflicts.
- This `handoff/` package is curated for CounterPro migration; re-verify against code before relying on fine detail.

---

## Multi-user / Dropbox SQLite limitation

BidTracker commonly shares one SQLite file via Dropbox. That is a desktop prototype constraint (locking, sync conflicts, path coupling) — **not** a model to recreate in CounterPro. CounterPro’s target is Supabase Postgres with proper migrations and auth.

Attachment / bid folder paths under Dropbox may not map 1:1 in a future migration (see [04-migration-to-counterpro/data-migration-notes.md](04-migration-to-counterpro/data-migration-notes.md)).

---

## Implication for CounterPro

When mapping concepts, treat gaps as **product decisions** (build, skip, or replace with an existing CounterPro report), not as silent requirements to clone unfinished BidTracker UI.
