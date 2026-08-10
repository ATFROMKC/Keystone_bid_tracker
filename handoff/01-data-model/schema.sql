-- Keystone Bid Tracker schema export
-- Generated from Database.init_db() (CREATE TABLE + ALTER migrations applied)
-- Source of truth: keystone_bid_tracker/database.py

-- table: bid_board_attachments
CREATE TABLE bid_board_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    label TEXT,
                    value TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );

-- table: bid_board_item_bids
CREATE TABLE bid_board_item_bids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(board_item_id, bid_id)
                );

-- table: bid_board_item_contacts
CREATE TABLE bid_board_item_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    customer_contact_id INTEGER NOT NULL REFERENCES customer_contacts(id) ON DELETE CASCADE
                );

-- table: bid_board_item_customers
CREATE TABLE bid_board_item_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    customer_id INTEGER NOT NULL REFERENCES customers(id)
                );

-- table: bid_board_items
CREATE TABLE bid_board_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_name TEXT NOT NULL,
                    board_date TEXT NOT NULL,
                    actual_due_date TEXT,
                    actual_due_time TEXT,
                    estimator TEXT,
                    board_status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
                    notes TEXT,
                    completed_at TEXT,
                    created_bid_id INTEGER REFERENCES bids(id),
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                , location TEXT, source TEXT DEFAULT 'LOCAL', outlook_event_id TEXT, outlook_calendar_id TEXT, outlook_last_modified TEXT, outlook_last_synced TEXT, outlook_source_notes TEXT);

-- table: bid_customers
CREATE TABLE bid_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_id INTEGER NOT NULL REFERENCES bids(id),
                    customer_id INTEGER NOT NULL REFERENCES customers(id)
                );

-- table: bid_moraware_allocations
CREATE TABLE bid_moraware_allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
                    moraware_job_id TEXT NOT NULL,
                    allocated_bid_total REAL NOT NULL DEFAULT 0,
                    allocated_solid_surf_sf REAL NOT NULL DEFAULT 0,
                    allocated_stone_sf REAL NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(bid_id, moraware_job_id),
                    FOREIGN KEY (bid_id, moraware_job_id)
                        REFERENCES bid_moraware_links(bid_id, moraware_job_id)
                        ON DELETE CASCADE
                );

-- table: bid_moraware_links
CREATE TABLE bid_moraware_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
                    moraware_job_id TEXT NOT NULL,
                    moraware_job_number TEXT,
                    moraware_job_name TEXT,
                    is_primary INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(bid_id, moraware_job_id)
                );

-- table: bid_revisions
CREATE TABLE bid_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_id INTEGER NOT NULL REFERENCES bids(id),
                    revision_no INTEGER NOT NULL DEFAULT 1,
                    revision_date TEXT NOT NULL,
                    bid_total REAL DEFAULT 0,
                    solid_surf_sf REAL DEFAULT 0,
                    stone_sf REAL DEFAULT 0,
                    reason TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

-- table: bids
CREATE TABLE bids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_name TEXT NOT NULL,
                    estimator TEXT NOT NULL,
                    original_bid_date TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    won_customer_id INTEGER REFERENCES customers(id),
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                , salesperson TEXT, project_manager TEXT, moraware_job_date TEXT, won_date TEXT, won_notes TEXT, moraware_job_id TEXT, moraware_job_number TEXT, moraware_job_status TEXT, last_moraware_sync_at TEXT, est_complete_date TEXT, est_complete_date_manual INTEGER DEFAULT 0, est_start_month TEXT, moraware_created_date TEXT, notebook_notes TEXT, parent_bid_id INTEGER REFERENCES bids(id), bid_role TEXT DEFAULT 'normal', exclude_from_rollups INTEGER DEFAULT 0, due_date TEXT, location TEXT);

-- table: customer_contacts
CREATE TABLE customer_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                    email TEXT NOT NULL,
                    name TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                );

-- table: customers
CREATE TABLE customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                );

-- table: estimators
CREATE TABLE estimators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT,
                    active INTEGER DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

-- table: invoice_data
CREATE TABLE invoice_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_id INTEGER NOT NULL REFERENCES bids(id),
                    moraware_job_id TEXT,
                    phase TEXT,
                    tp_code REAL,
                    sq_ft REAL,
                    invoice_date TEXT,
                    template_date TEXT,
                    install_date TEXT,
                    contact_customer_date TEXT,
                    contact_customer_notes TEXT,
                    invoice_status TEXT,
                    source TEXT,
                    synced_at TEXT DEFAULT (datetime('now'))
                );

-- index: idx_bid_board_attachments_item
CREATE INDEX idx_bid_board_attachments_item ON bid_board_attachments(board_item_id);

-- index: idx_bid_board_item_bids_bid
CREATE INDEX idx_bid_board_item_bids_bid ON bid_board_item_bids(bid_id);

-- index: idx_bid_board_item_bids_item
CREATE INDEX idx_bid_board_item_bids_item ON bid_board_item_bids(board_item_id);

-- index: idx_bid_board_item_contacts_item
CREATE INDEX idx_bid_board_item_contacts_item ON bid_board_item_contacts(board_item_id);

-- index: idx_bid_board_item_customers_item
CREATE INDEX idx_bid_board_item_customers_item ON bid_board_item_customers(board_item_id);

-- index: idx_bid_board_items_board_date
CREATE INDEX idx_bid_board_items_board_date ON bid_board_items(board_date);

-- index: idx_bid_board_items_board_status
CREATE INDEX idx_bid_board_items_board_status ON bid_board_items(board_status);

-- index: idx_bid_board_items_estimator
CREATE INDEX idx_bid_board_items_estimator ON bid_board_items(estimator);

-- index: idx_bid_moraware_allocations_bid_id
CREATE INDEX idx_bid_moraware_allocations_bid_id ON bid_moraware_allocations(bid_id);

-- index: idx_bid_moraware_links_bid_id
CREATE INDEX idx_bid_moraware_links_bid_id ON bid_moraware_links(bid_id);

-- index: idx_bid_moraware_links_job_id
CREATE INDEX idx_bid_moraware_links_job_id ON bid_moraware_links(moraware_job_id);

-- index: idx_bid_moraware_links_primary
CREATE UNIQUE INDEX idx_bid_moraware_links_primary
                    ON bid_moraware_links(bid_id) WHERE is_primary = 1;

-- index: idx_bid_revisions_bid_id_revision_no
CREATE INDEX idx_bid_revisions_bid_id_revision_no ON bid_revisions(bid_id, revision_no);

-- index: idx_bids_bid_role
CREATE INDEX idx_bids_bid_role ON bids(bid_role);

-- index: idx_bids_exclude_rollups
CREATE INDEX idx_bids_exclude_rollups ON bids(exclude_from_rollups);

-- index: idx_bids_moraware_job_id
CREATE INDEX idx_bids_moraware_job_id ON bids(moraware_job_id);

-- index: idx_bids_moraware_job_status
CREATE INDEX idx_bids_moraware_job_status ON bids(moraware_job_status);

-- index: idx_bids_original_bid_date
CREATE INDEX idx_bids_original_bid_date ON bids(original_bid_date);

-- index: idx_bids_parent_bid_id
CREATE INDEX idx_bids_parent_bid_id ON bids(parent_bid_id);

-- index: idx_bids_status
CREATE INDEX idx_bids_status ON bids(status);

-- index: idx_board_outlook_event
CREATE UNIQUE INDEX idx_board_outlook_event
                    ON bid_board_items(outlook_calendar_id, outlook_event_id)
                    WHERE outlook_event_id IS NOT NULL;

-- index: idx_customer_contacts_customer
CREATE INDEX idx_customer_contacts_customer ON customer_contacts(customer_id);

-- index: idx_estimators_name
CREATE INDEX idx_estimators_name ON estimators(name);

-- index: idx_invoice_data_bid_id
CREATE INDEX idx_invoice_data_bid_id ON invoice_data(bid_id);

-- index: idx_invoice_data_bid_job_phase
CREATE INDEX idx_invoice_data_bid_job_phase ON invoice_data(bid_id, moraware_job_id, phase);

-- =============================================================================
-- Effective columns (after ALTER migrations)
-- =============================================================================
-- TABLE bid_board_attachments
--   id INTEGER PRIMARY KEY
--   board_item_id INTEGER NOT NULL
--   kind TEXT NOT NULL
--   label TEXT
--   value TEXT NOT NULL
--   created_at TEXT DEFAULT datetime('now')

-- TABLE bid_board_item_bids
--   id INTEGER PRIMARY KEY
--   board_item_id INTEGER NOT NULL
--   bid_id INTEGER NOT NULL
--   created_at TEXT DEFAULT datetime('now')

-- TABLE bid_board_item_contacts
--   id INTEGER PRIMARY KEY
--   board_item_id INTEGER NOT NULL
--   customer_contact_id INTEGER NOT NULL

-- TABLE bid_board_item_customers
--   id INTEGER PRIMARY KEY
--   board_item_id INTEGER NOT NULL
--   customer_id INTEGER NOT NULL

-- TABLE bid_board_items
--   id INTEGER PRIMARY KEY
--   bid_name TEXT NOT NULL
--   board_date TEXT NOT NULL
--   actual_due_date TEXT
--   actual_due_time TEXT
--   estimator TEXT
--   board_status TEXT NOT NULL DEFAULT 'IN_PROGRESS'
--   notes TEXT
--   completed_at TEXT
--   created_bid_id INTEGER
--   created_at TEXT DEFAULT datetime('now')
--   updated_at TEXT DEFAULT datetime('now')
--   location TEXT
--   source TEXT DEFAULT 'LOCAL'
--   outlook_event_id TEXT
--   outlook_calendar_id TEXT
--   outlook_last_modified TEXT
--   outlook_last_synced TEXT
--   outlook_source_notes TEXT

-- TABLE bid_customers
--   id INTEGER PRIMARY KEY
--   bid_id INTEGER NOT NULL
--   customer_id INTEGER NOT NULL

-- TABLE bid_moraware_allocations
--   id INTEGER PRIMARY KEY
--   bid_id INTEGER NOT NULL
--   moraware_job_id TEXT NOT NULL
--   allocated_bid_total REAL NOT NULL DEFAULT 0
--   allocated_solid_surf_sf REAL NOT NULL DEFAULT 0
--   allocated_stone_sf REAL NOT NULL DEFAULT 0
--   created_at TEXT DEFAULT datetime('now')
--   updated_at TEXT DEFAULT datetime('now')

-- TABLE bid_moraware_links
--   id INTEGER PRIMARY KEY
--   bid_id INTEGER NOT NULL
--   moraware_job_id TEXT NOT NULL
--   moraware_job_number TEXT
--   moraware_job_name TEXT
--   is_primary INTEGER NOT NULL DEFAULT 0
--   created_at TEXT DEFAULT datetime('now')
--   updated_at TEXT DEFAULT datetime('now')

-- TABLE bid_revisions
--   id INTEGER PRIMARY KEY
--   bid_id INTEGER NOT NULL
--   revision_no INTEGER NOT NULL DEFAULT 1
--   revision_date TEXT NOT NULL
--   bid_total REAL DEFAULT 0
--   solid_surf_sf REAL DEFAULT 0
--   stone_sf REAL DEFAULT 0
--   reason TEXT
--   created_at TEXT DEFAULT datetime('now')

-- TABLE bids
--   id INTEGER PRIMARY KEY
--   bid_name TEXT NOT NULL
--   estimator TEXT NOT NULL
--   original_bid_date TEXT NOT NULL
--   status TEXT DEFAULT 'PENDING'
--   won_customer_id INTEGER
--   notes TEXT
--   created_at TEXT DEFAULT datetime('now')
--   salesperson TEXT
--   project_manager TEXT
--   moraware_job_date TEXT
--   won_date TEXT
--   won_notes TEXT
--   moraware_job_id TEXT
--   moraware_job_number TEXT
--   moraware_job_status TEXT
--   last_moraware_sync_at TEXT
--   est_complete_date TEXT
--   est_complete_date_manual INTEGER DEFAULT 0
--   est_start_month TEXT
--   moraware_created_date TEXT
--   notebook_notes TEXT
--   parent_bid_id INTEGER
--   bid_role TEXT DEFAULT 'normal'
--   exclude_from_rollups INTEGER DEFAULT 0
--   due_date TEXT
--   location TEXT

-- TABLE customer_contacts
--   id INTEGER PRIMARY KEY
--   customer_id INTEGER NOT NULL
--   email TEXT NOT NULL
--   name TEXT
--   active INTEGER DEFAULT 1
--   created_at TEXT DEFAULT datetime('now')

-- TABLE customers
--   id INTEGER PRIMARY KEY
--   name TEXT NOT NULL
--   active INTEGER DEFAULT 1
--   created_at TEXT DEFAULT datetime('now')

-- TABLE estimators
--   id INTEGER PRIMARY KEY
--   name TEXT NOT NULL
--   color TEXT
--   active INTEGER DEFAULT 1
--   sort_order INTEGER DEFAULT 0
--   created_at TEXT DEFAULT datetime('now')

-- TABLE invoice_data
--   id INTEGER PRIMARY KEY
--   bid_id INTEGER NOT NULL
--   moraware_job_id TEXT
--   phase TEXT
--   tp_code REAL
--   sq_ft REAL
--   invoice_date TEXT
--   template_date TEXT
--   install_date TEXT
--   contact_customer_date TEXT
--   contact_customer_notes TEXT
--   invoice_status TEXT
--   source TEXT
--   synced_at TEXT DEFAULT datetime('now')
