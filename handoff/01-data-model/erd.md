# ER diagram (BidTracker)

Mermaid ER for current SQLite schema. Source: `keystone_bid_tracker/database.py` / [schema.sql](schema.sql).

```mermaid
erDiagram
  customers ||--o{ bid_customers : has
  customers ||--o{ customer_contacts : has
  customers ||--o{ bid_board_item_customers : linked
  customers ||--o{ bids : won_by

  bids ||--o{ bid_customers : accounts
  bids ||--o{ bid_revisions : revisions
  bids ||--o{ invoice_data : phases
  bids ||--o{ bid_moraware_links : links
  bids ||--o{ bid_moraware_allocations : allocations
  bids ||--o{ bid_board_item_bids : board_links
  bids ||--o| bids : parent_child

  bid_moraware_links ||--o| bid_moraware_allocations : per_job

  bid_board_items ||--o{ bid_board_item_customers : accounts
  bid_board_items ||--o{ bid_board_item_contacts : recipients
  bid_board_items ||--o{ bid_board_attachments : files_links
  bid_board_items ||--o{ bid_board_item_bids : bids
  customer_contacts ||--o{ bid_board_item_contacts : picked

  estimators ||--o{ bid_board_items : assigned

  customers {
    int id PK
    text name UK
    int active
  }

  bids {
    int id PK
    text bid_name
    text estimator
    text original_bid_date
    text status
    int won_customer_id FK
    text won_date
    text moraware_job_id
    text moraware_job_number
    text moraware_created_date
    text est_complete_date
    int est_complete_date_manual
    text est_start_month
    int parent_bid_id FK
    text bid_role
    int exclude_from_rollups
  }

  bid_revisions {
    int id PK
    int bid_id FK
    int revision_no
    real bid_total
    real solid_surf_sf
    real stone_sf
  }

  bid_moraware_links {
    int id PK
    int bid_id FK
    text moraware_job_id
    int is_primary
  }

  bid_moraware_allocations {
    int id PK
    int bid_id FK
    text moraware_job_id
    real allocated_bid_total
  }

  invoice_data {
    int id PK
    int bid_id FK
    text moraware_job_id
    text phase
    real tp_code
    real sq_ft
    text invoice_status
    text invoice_date
  }

  bid_board_items {
    int id PK
    text bid_name
    text board_date
    text board_status
    text source
    text outlook_event_id
    text outlook_calendar_id
  }

  estimators {
    int id PK
    text name UK
    text color
  }
```

## Relationship notes

- **Financials** hang off `bid_revisions`, not `bids`.
- **Board authority** for linked bids is `bid_board_item_bids` (not legacy `created_bid_id`).
- **Moraware authority** for multi-link is `bid_moraware_links`; `bids.moraware_job_id` mirrors primary.
- **Allocations** FK to `(bid_id, moraware_job_id)` on links.
- Outlook uniqueness: unique index on `(outlook_calendar_id, outlook_event_id)` where event id is present.
