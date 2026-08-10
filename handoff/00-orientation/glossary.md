# Glossary

Terms as used in BidTracker today. Do not conflate these when mapping to CounterPro.

| Term | Meaning |
|---|---|
| **Account / Customer** | Row in `customers`. A company/account that can be linked to bids and board items. |
| **Contact** | Email (+ optional name) on an account (`customer_contacts`). Reusable; board items pick subsets. |
| **Bid** | A normal BidTracker pricing record (`bids`) with status, estimator, dates, optional Moraware links. Financials live on **revisions**, not on the bid row. |
| **Revision** | A versioned pricing snapshot on a bid (`bid_revisions`: `bid_total`, `solid_surf_sf`, `stone_sf`, reason, date). **Latest revision** = highest `revision_no`. |
| **Bid Board item / Opportunity** | Calendar estimating task (`bid_board_items`). Not a bid. Status: `IN_PROGRESS`, `COMPLETE`, `NOT_BIDDING`. |
| **Board ↔ Bid link** | Many-to-many via `bid_board_item_bids`. One opportunity → zero/one/many independent bids (alternate materials/pricing/accounts). **Not** revisions. |
| **`created_bid_id`** | Legacy single FK on board items; backfilled into join table. **Not** authority. |
| **Moraware job** | ERP job. Identified by internal **`moraware_job_id`** and display **`moraware_job_number`** — different values; never infer one from the other. |
| **Bid ↔ Moraware link** | Many-to-many (`bid_moraware_links`) with exactly one **primary** link per bid when linked. Legacy `bids.moraware_job_id` mirrors primary. |
| **Allocation** | Dollars/SF split across linked Moraware jobs (`bid_moraware_allocations`). Sums must match latest revision totals (±$0.01). |
| **Parent / Child bid** | After split: parent `bid_role='parent'`, `exclude_from_rollups=1`; children are normal WON bids each with one primary Moraware link. |
| **Invoice / phase data** | Cached Moraware phase rows (`invoice_data`): TP, SF, template/install/invoice dates, invoice status. Job type (Stone / Solid Surface / Mixed) is **derived**, not stored. |
| **Active Jobs** | PM list driven by Moraware status buckets (Active / Unscheduled / 30+ Days Old) with local link overlay. |
| **Pending Award** | Local WON bids with no Moraware link. |
| **Date Won (`won_date`)** | Canonical local won date. Separate from `moraware_created_date`. Clamp: never later than Moraware created date when both exist. |
| **Estimator (roster)** | Named estimator with optional color (`estimators` table + config overrides). Distinct from CounterPro `staff_members`. |
| **Outlook-sourced board item** | Board row with `source='OUTLOOK'` upserted by read-only sync; never auto-deleted; local COMPLETE never undone by Outlook. |

## Orthogonal lifecycles (easy to get wrong)

- Board **COMPLETE** ≠ Bid **WON**.
- Linking a Moraware job does not create a board item.
- Unlinking a board bid or unsyncing Moraware does not delete the bid (unless a dedicated “move back” path clears won state).
