# Data migration notes (SQLite → Supabase)

**Bottom line:** Move BidTracker data into CounterPro via additive `database/migrations/` only. Map onto existing Moraware caches — do not parallel them. No destructive migrations without Chip’s sign-off. Prefer identity ties to staff/auth over inventing new people tables.

This is guidance for a future migration, not a runnable script. Inspect CounterPro schema before writing migrations.

---

## Principles

| Rule | Detail |
|---|---|
| Path | SQLite (`keystone_bid_tracker` / shared Dropbox DB) → Supabase Postgres |
| Migrations | New files under CounterPro `database/migrations/` |
| Additive only | Prefer CREATE / ALTER ADD; avoid DROP / rewrite of existing rows |
| Destructive | Requires Chip’s explicit sign-off (PR DoD) |
| Moraware truth | ERP remains truth; Supabase stays a cache with sync windows |
| Secrets | Never put Moraware/Outlook/Supabase credentials in migrations or fixtures |

---

## Moraware-related data

- **Map** BidTracker `invoice_data` / phase rows onto existing Moraware-cache tables. Do **not** create a parallel invoice/phase cache.
- Always migrate **both** `moraware_job_id` and `moraware_job_number` (different values; never infer one from the other).
- Respect the **multi-phase first-invoice-date pitfall**: several CounterPro caches key on the first phase’s invoice date; later phases can be invisible. Do not “fix” gaps by rounding. Reconcile BidTracker’s per-phase model with CounterPro’s cache assumptions.
- Job Ticket A / per-phase dollars & SF are ERP concepts CounterPro already understands — align imports with that model rather than inventing a third shape.
- After import, treat cache freshness as unproven until a CounterPro sync path confirms it. Silence ≠ zero.

---

## People and auth

- Tie BidTracker estimators / local users to CounterPro **staff** and **auth** — do not recreate a parallel user roster as system of record.
- Commercial vs residential / location splits must continue to flow only through `staff_members.is_commercial` + `showroom_location` / `staffService.ts`.

---

## Bid / board domain (likely net-new tables)

After audit (especially retired commercial estimator), genuine Adds may include bids, revisions, board items, board↔bid links, bid↔job links, allocations, parent/child metadata.

When migrating:

- Preserve invariants (one primary Moraware link when linked; allocation sums; WON not deletable; parent excluded from rollups).
- Prefer stable natural keys + explicit ID maps over silent SQLite integer PK reuse where FKs cross systems.
- Board COMPLETE ≠ bid WON — keep lifecycles orthogonal in the target schema.

---

## Outlook

- Prefer **Microsoft Graph** event / calendar IDs as the long-term upsert key (BidTracker already implements Graph; COM EntryIDs are Classic-desktop-specific).
- Do not assume COM EntryIDs survive or are useful on Render-hosted CounterPro.
- Preserve read-only semantics: never auto-delete local board rows from Outlook; never undo local COMPLETE from sync.

---

## Attachments / Dropbox

- BidTracker often stores Dropbox-relative or local paths. These **may not map 1:1** to CounterPro storage.
- Plan an explicit file-storage strategy (existing portal pattern if any) rather than copying path strings blindly.
- Multi-user Dropbox SQLite is a BidTracker limitation, not a CounterPro pattern — migration is also an opportunity to leave that model behind.

---

## PostgREST / query limits

- PostgREST caps results at **1000** rows (`.limit()` and `.range()`). Large backfills and verification queries must paginate (ordered pages) or use RPC.
- Count before bulk UPDATE/DELETE; batch and cap; never unbounded cleanup at boot.

---

## Suggested migration order (non-binding)

1. Staff/auth identity map for estimators  
2. Accounts/contacts (Map/Reuse existing customer model if present)  
3. Confirm Moraware job identity map (both IDs) — no parallel job cache  
4. Bids → revisions → board items → links → allocations / splits  
5. Phase/invoice fields → Map into existing caches (or refresh via CounterPro sync instead of bulk import where safer)  
6. Outlook Graph IDs / board source metadata  
7. Attachments last (storage remapping)

---

## Related

- Destination rules: [counterpro-destination-context.md](counterpro-destination-context.md)
- Worksheet: [concept-mapping-worksheet.md](concept-mapping-worksheet.md)
- Gaps: [../05-known-gaps.md](../05-known-gaps.md)
