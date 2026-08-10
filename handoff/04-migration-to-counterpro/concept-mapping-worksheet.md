# Concept mapping worksheet

**Bottom line:** Fill CounterPro equivalent + Classification after inspecting CounterPro. Default hypotheses are informed guesses — **verify**, then overwrite. Do not invent CounterPro table names beyond what Chip’s docs already name.

Framework: [reuse-extend-map-add.md](reuse-extend-map-add.md). Process: [inspect-first-process.md](inspect-first-process.md).

Classification values: `Reuse` | `Map` | `Extend` | `Add` | `Audit-first` (confirm with Chip before coding).

---

## Worksheet

| Concept | BidTracker facts | Default hypothesis (verify) | CounterPro equivalent (fill) | Classification (fill) | Notes |
|---|---|---|---|---|---|
| Estimators / Users | Local `estimators` roster + config colors; not full auth | **Reuse** staff/auth; do not invent parallel users | | | Tie estimator identity to existing staff/auth |
| Accounts | `customers` table; company/account linked to bids & board | Verify — may Map/Reuse existing customer model | | | Inspect before Add |
| Contacts | `customer_contacts` (email + optional name); board picks subsets | Verify — Map/Extend if contacts exist | | | |
| Bids | `bids`: PENDING/BIDDING/WON; financials on revisions; parents excluded from rollups | **Likely Add after audit** | | | Audit retired commercial estimator first |
| Revisions | `bid_revisions`; latest = max `revision_no` | **Likely Add after audit** | | | |
| Board Items | `bid_board_items` opportunities; IN_PROGRESS/COMPLETE/NOT_BIDDING | **Likely Add after audit** | | | Orthogonal to bid WON |
| Board–Bid links | M:N `bid_board_item_bids`; legacy `created_bid_id` not authority | **Likely Add after audit** | | | Multi-bid per opportunity ≠ revisions |
| Attachments | Bid/board file paths (often Dropbox) | Verify path/storage model | | | Paths may not map 1:1 |
| Moraware Jobs | ERP jobs; dual IDs (`moraware_job_id` + `moraware_job_number`) | **Reuse** Moraware via backend+cli+azure | | | Never port BidTracker client |
| Bid–Job links | M:N `bid_moraware_links`; one primary when linked | Likely Add (join) on Reused jobs | | | |
| Allocations | `bid_moraware_allocations`; sums match latest revision (±$0.01) | **Likely Add after audit** | | | |
| Parent/Child splits | Parent `bid_role='parent'`, `exclude_from_rollups=1`; children WON + primary link | **Likely Add after audit** | | | |
| invoice_data / phases | Local cache: TP, SF, dates, invoice_status; job type derived | **Map** onto Moraware-cache tables | | | Multi-phase first-invoice-date pitfall |
| Active Jobs | PM list from Moraware active buckets + local link overlay | Reuse Moraware list + overlay Add/Extend | | | |
| Pending Award | Local WON bids with no Moraware link | Likely Add query/UI (partial in BidTracker) | | | See known gaps |
| Completed History | Local `invoice_data` rollups | Map cache + Add UI as needed (partial) | | | |
| Pipeline forecast | Logic exists; `PMOverviewTab` unwired | Verify reporting surfaces; may Add UI | | | See known gaps |
| Outlook sync | Read-only upsert to board; COM workaround; Graph intended | **Add** Graph server-side (COM reference only) | | | Same Azure AD plane as CounterPro |
| Reporting | Estimator reports; `get_pm_monthly_report` no UI | Reuse/Extend portal reporting where possible | | | |
| Config / Secrets | Local gitignored `config.json` | Map to portal settings / env (Chip-owned secrets) | | | Two settings tables; no prod creds in repo |
| Staff commercial routing | BidTracker has no `staffService` equivalent | **Reuse** `staff_members` + `staffService.ts` | | | Never parse names/addresses |
| Retired commercial estimator (CounterPro) | N/A in BidTracker | **Audit-first** — do not build on without Chip | `commercialEstimatingService.ts` / routes (named in Chip docs) | Audit-first | Highest anti-duplication check |

---

## How to use

1. Inspect CounterPro (step 2 of inspect-first).
2. Replace “Default hypothesis” with verified Classification.
3. Fill CounterPro equivalent with **inspected** paths/tables only — leave blank rather than invent.
4. Get Chip review for frozen areas, destructive migrations, or estimator revival.
5. Implement Adds/Extends in CounterPro style.
