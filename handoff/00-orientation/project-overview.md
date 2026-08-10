# Project overview (BidTracker today)

## Bottom line

**Keystone Bid Tracker** is a Windows **PyQt5 desktop** app for commercial bid tracking and PM workflows. It uses a shared **SQLite** database (commonly on Dropbox). It is the working prototype / source of truth for commercial estimating and bid-management behavior that may later live inside the Keystone Pricing Portal (CounterPro).

Entry point: `keystone_bid_tracker/main.py`  
App version constant: `1.0.0`  
Stack: Python, PyQt5, SQLite

## Portal model

Three top-level portals (switched via `PortalController` in `main.py`; last portal persisted in config):

| Portal | Role | Maturity |
|---|---|---|
| **Hub** | Settings, customers/accounts, navigation into Estimator/PM | Stable enough for config |
| **Estimator** | Bids, revisions, Bid Board calendar, reports, Outlook sync | Most stable daily-use area |
| **PM** | Active Jobs (Moraware-driven), Pending Award, Completed History | Evolving; Pending Award & Completed History still partial |

## What it does (capabilities)

- Track **bids**, **revisions**, statuses (`PENDING` / `BIDDING` / `WON`), and **accounts** (customers).
- **Bid Board**: calendar of estimating *opportunities*; one opportunity can link **zero, one, or many** normal bids (not revisions).
- **Outlook → Bid Board** one-way read-only sync (Classic COM workaround today; Graph intended after admin consent).
- Link bids to **Moraware jobs** (many-to-many primary/secondary), sync invoice/phase data, split allocations / parent-child bids.
- PM views: Active Jobs overlay, Pending Award (WON unlinked), Completed History, pipeline forecast logic (UI partially unwired — see [05-known-gaps.md](../05-known-gaps.md)).

## What it does not do

- It is not CounterPro and does not replace CounterPro’s Moraware, staff, pricing, or auth systems.
- It does not write to Outlook.
- Moraware writes are not BidTracker’s job; the client is read-oriented (login + read/sync).

## Source-of-truth order (inside this repo)

1. Code under `keystone_bid_tracker/`
2. `PROJECT_CONTEXT.md`
3. `SESSION_NOTES.md`
4. This `handoff/` package (curated for CounterPro migration)
5. Legacy docs under `docs/` / `reference/` (historical)

## Related docs

- Glossary: [glossary.md](glossary.md)
- Architecture: [architecture.md](architecture.md)
- Known gaps: [../05-known-gaps.md](../05-known-gaps.md)
