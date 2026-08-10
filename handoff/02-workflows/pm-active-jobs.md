# PM Active Jobs

**Bottom line:** Active Jobs is a **Moraware-driven** worklist (job statuses Active / Unscheduled / 30+ Days Old) with a **local link overlay**. Reloading the job list is read-only; refreshing a job syncs invoice/phase cache into SQLite. Linking requires a local bid; a linked non-WON bid is flagged as a **mismatch**.

> **Framing:** WHAT / WHY is authoritative. BidTracker’s Moraware HTTP client is **not** to be ported — CounterPro already owns Moraware. Use this doc for PM UX rules and link semantics only.

---

## WHAT / WHY (business rules)

### Source of truth for the grid

- Rows come from Moraware job-list filters that match the shop’s Active Jobs view:
  - **Active**
  - **Unscheduled**
  - **30+ Days Old**
- Local SQLite does **not** invent these rows. The UI overlays:
  - whether a local bid is linked to that `moraware_job_id`
  - bid name / status / won account
  - **mismatch** when a link exists but the local bid `status != WON`

### Link overlay

- Linking attaches the Moraware job to a local bid via `bid_moraware_links` (and mirrors primary onto `bids.moraware_job_id`).
- Typical link path also ensures the bid is WON with a chosen account (review dialog / mark-won), salesperson/PM from Moraware when available.
- **Mismatch** = linked but not WON — visible warning so PMs fix status before treating the job as awarded locally.

### Refresh modes (do not conflate)

| Action | Network | DB writes | Purpose |
|---|---|---|---|
| **Reload Job List** | Fetches Moraware job list | **No** invoice/DB writes for phases | Refresh which jobs appear / metadata in session |
| **Refresh Job** | Fetches invoice/phase detail for one linked job | **Yes** — upserts `invoice_data`, updates Moraware metadata timestamps/status | Sync one bid’s phase cache |
| **Refresh All Jobs** | Same as Refresh Job for all linked jobs in the current list | **Yes** — batch invoice sync | Catch up caches after reload |

Awarded-tab helpers reuse the same invoice sync pattern (`sync_invoice_data_fast` → `upsert_invoice_data`).

### Session cache

- PM window holds an in-memory `active_jobs_session_cache` (`jobs`, `fetched_at`).
- Switching tabs / reopening Active Jobs can reuse the session list without hitting Moraware until Reload.
- Cache is **process session** only — not durable across app restarts.

### Context menu (behavioral contract)

Typical actions on a row:

- **Open in Moraware** — browser to `{moraware_url_origin}/sys/job/{job_id}`
- **Link to Local Bid…** — picker + review (account mismatch handling)
- **Add Another Job to This Quote…** — secondary Moraware link on an existing linked bid
- **Refresh Job** — invoice sync for that bid
- **Split Bid from Moraware Jobs…** — allocation/split workflow (see linking-splits)
- **Unsync from Moraware** — clear links/invoice cache; **keep** WON/PENDING status
- **Edit Job** — local won/PM fields (est complete, start month, etc.)
- **Move Back to Bidding** — clear won + Moraware state → `PENDING` (destructive vs unsync)

Unlinked rows only enable Open / Link (other actions need a `bid_id`).

---

## HOW BidTracker does it (reference)

| Concern | Path |
|---|---|
| Active Jobs UI | `ui/pm_active_jobs_tab.py` |
| Session cache owner | `ui/main_window.py` → `PMWindow.active_jobs_session_cache` |
| Link picker | `ui/link_local_bid_dialog.py` |
| Link review / account mismatch | `ui/link_review_dialog.py` |
| Invoice sync helpers (shared) | `ui/awarded_tab.py` workers / patterns; `utils/moraware_client.py` list filters |
| Open URL | `pm_active_jobs_tab.py` → `_open_in_moraware` |

Moraware list filter codes (reference only): Active / Unscheduled / 30+ Days Old constructed in `utils/moraware_client.py` to match Moraware’s job-list UI.

---

## Invariants to preserve in CounterPro

1. Grid membership = Moraware statuses; local DB is overlay + cache.
2. Reload list ≠ invoice sync.
3. Mismatch when linked bid is not WON.
4. Open-in-Moraware uses ERP job id in `/sys/job/{id}`, not job number.
5. Do not reimplement BidTracker’s credentialed Moraware session client in CounterPro.
