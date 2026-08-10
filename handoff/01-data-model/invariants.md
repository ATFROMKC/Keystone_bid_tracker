# Data invariants (BidTracker)

These are business / integrity rules the app enforces or relies on. Preserve the **intent** in CounterPro even if the implementation differs.

## Bids & revisions

1. New bids default to **`PENDING`**; financials start as **revision 1**.
2. Displayed totals/SF always come from the **latest revision** (`MAX(revision_no)`).
3. **WON bids cannot be deleted** (UI + `delete_bid`).
4. Editing bid totals in the edit dialog only writes revision 1 when it is the **sole** revision.
5. Rows with **`bid_role = 'parent'`** are excluded from normal bid lists / Pending Award.
6. Rollups filter **`exclude_from_rollups = 0`** (parents after split).
7. Legacy statuses **`LOST` / `DEAD`** are migrated to `PENDING` on init.
8. Account report quirk: a WON bid may display as **`BIDDING`** for a linked non-winning account (`won_customer_id` mismatch).

## Bid Board

9. Board item ≠ bid. Authority for links is **`bid_board_item_bids`**, not `created_bid_id`.
10. Multiple linked bids are **independent pricing paths**, not revisions.
11. **COMPLETE** only on explicit Finish / Mark Complete — not merely logging a bid.
12. Board **COMPLETE ≠** bid **WON** (orthogonal lifecycles).
13. Unlink board bid does **not** delete the bid; status may stay COMPLETE.
14. Drag-and-drop changes **`board_date` only**.
15. Outlook may promote COMPLETE; **never demotes** local COMPLETE. Linked bids can block Outlook **NOT_BIDDING** override.
16. Outlook-sourced rows are **never auto-deleted** by sync. `source=LOCAL` never pushed to Outlook.

## Moraware linking & allocations

17. At most **one primary** Moraware link per bid (partial unique index).
18. `bids.moraware_job_id` / `moraware_job_number` **mirror primary** link.
19. **`moraware_job_id` and `moraware_job_number` are different**; never infer one from the other. Always store/display both when known.
20. Allocation sums must equal latest revision totals (**± $0.01** / SF) before save / split.
21. Split: parent becomes historical container (`bid_role='parent'`, `exclude_from_rollups=1`); children get their own links/invoice rows.
22. Child bids cannot be split again.
23. **Unsync** removes links/allocations/invoice_data but can keep WON. **Move back to bidding** clears won fields + links + invoices → PENDING.

## Dates & PM

24. **`won_date`** is canonical Date Won. Backfill from `moraware_created_date` when blank; **clamp** if `won_date > moraware_created_date`.
25. **`est_complete_date`** auto = `MAX(install_date)` on invoice upsert unless `est_complete_date_manual = 1`.
26. **`est_start_month`** does not remove a job from Moraware Unscheduled visibility.
27. Job type is **derived** (phase prefix SS/ST or revision SF), never stored.
28. Invoice status complete matching uses normalized `LOWER(TRIM(...)) = 'complete'`.
29. Combined invoice activities (e.g. `ST1, ST2`) reconcile onto individual Job Ticket A phases — no synthetic combined phase row.
30. Only Invoice activity rows set `invoice_status` / `invoice_date`; Template/Install/Contact must not downgrade completed phases.

## Refresh semantics

31. **Reload Job List** = Moraware list only; **no** local metadata writes.
32. **Refresh Job / Refresh All** = sync invoice + linked metadata for WON/linked bids.

## CounterPro-facing note

When mapping these invariants, prefer **Reuse/Map** onto existing Moraware-cache and staff systems. Do not invent a second Moraware client or a parallel invoice cache that disagrees with CounterPro sync windows. Multi-phase commercial jobs: if CounterPro caches key the **first** phase invoice date, reconcile BidTracker’s per-phase model carefully — do not “round away” later phases.
