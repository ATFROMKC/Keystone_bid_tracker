# Schema reference (BidTracker)

Authoritative schema lives in `keystone_bid_tracker/database.py` (`init_db()`). Portable dump: [schema.sql](schema.sql). ER diagram: [erd.md](erd.md).

## Design notes (WHAT)

- **Financials** are versioned on `bid_revisions`, not on `bids`.
- **Board** and **bid** are separate entities; many-to-many via `bid_board_item_bids`.
- **Moraware** multi-link is `bid_moraware_links` (+ allocations); `bids.moraware_job_id` / `moraware_job_number` mirror the **primary** link for legacy queries.
- Migrations are additive `ALTER TABLE ... ADD COLUMN` with duplicate-column ignore, plus backfills (board bid join, Moraware links from legacy columns, allocation seed).

## Tables

### `customers`

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT UNIQUE NOT NULL | Account display name |
| active | INTEGER DEFAULT 1 | Inactive hidden from pickers |
| created_at | TEXT | |

### `customer_contacts`

| Column | Notes |
|---|---|
| id, customer_id FK, email NOT NULL, name, active, created_at | Emails reusable across board items |

### `bids`

Core: `bid_name`, `estimator`, `original_bid_date`, `status` DEFAULT `'PENDING'`, `won_customer_id`, `notes`, `created_at`.

Added by migration (effective columns also in schema.sql pragma dump):

| Column | Meaning |
|---|---|
| salesperson, project_manager | Often overwritten from Moraware on link/refresh |
| won_date, won_notes | Canonical date won |
| moraware_job_id, moraware_job_number, moraware_job_status | Legacy primary mirror + status |
| last_moraware_sync_at | |
| moraware_created_date | Moraware created date (separate from won_date) |
| moraware_job_date | Legacy/compatibility only |
| est_complete_date, est_complete_date_manual | Auto from MAX(install_date) unless manual=1 |
| est_start_month | `YYYY-MM-01` forecast for unscheduled |
| notebook_notes | PM notes |
| parent_bid_id, bid_role (`normal`/`parent`/`child`), exclude_from_rollups | Split model |
| due_date, location | Optional; can copy from board on Complete Bid |

### `bid_customers`

Many-to-many bid ↔ account. ≥1 required on create.

### `bid_revisions`

| Column | Notes |
|---|---|
| bid_id, revision_no, revision_date | Rev 1 created with bid |
| bid_total, solid_surf_sf, stone_sf | Pricing / SF |
| reason | Optional on later revs |

### `invoice_data`

Per-phase Moraware cache for a bid (and tagged `moraware_job_id` when multi-link):

`phase`, `tp_code`, `sq_ft`, `invoice_date`, `template_date`, `install_date`, `contact_customer_date`, `contact_customer_notes`, `invoice_status`, `source`, `synced_at`.

### `bid_moraware_links`

`UNIQUE(bid_id, moraware_job_id)`; partial unique index: one `is_primary=1` per bid. Also stores `moraware_job_number`, `moraware_job_name`.

### `bid_moraware_allocations`

Per linked job: `allocated_bid_total`, `allocated_solid_surf_sf`, `allocated_stone_sf`. FK to links. Sums must match latest revision (±$0.01) on save.

### `bid_board_items`

Opportunity: `bid_name`, `board_date`, `actual_due_date`, `actual_due_time`, `estimator`, `board_status` DEFAULT `IN_PROGRESS`, `notes`, `completed_at`, legacy `created_bid_id`, `location`, Outlook fields (`source`, `outlook_event_id`, `outlook_calendar_id`, `outlook_last_modified`, `outlook_last_synced`, `outlook_source_notes`).

### Join / side tables

| Table | Role |
|---|---|
| `bid_board_item_customers` | Accounts on opportunity |
| `bid_board_item_contacts` | Selected recipient contacts |
| `bid_board_attachments` | `kind`, `label`, `value` |
| `bid_board_item_bids` | Authority for board↔bid; UNIQUE(board_item_id, bid_id) |
| `estimators` | Roster: name, color, active, sort_order |

## Important indexes

- Bids: status, moraware_job_id/status, original_bid_date, parent_bid_id, bid_role, exclude_from_rollups
- Invoice: bid_id; (bid_id, moraware_job_id, phase)
- Links: bid_id, job_id; unique primary per bid
- Board: board_date, board_status, estimator; unique Outlook (calendar_id, event_id) where event present
- Board bids: item and bid indexes

## Implementation reference

See `Database.init_db()` and method names in `keystone_bid_tracker/database.py`. Do not treat SQLite DDL as CounterPro migration SQL — translate through CounterPro’s `database/migrations/` conventions after inspecting existing tables.
