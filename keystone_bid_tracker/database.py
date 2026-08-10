"""
Keystone Bid Tracker - Database Layer
All SQLite CRUD operations for bids, customers, revisions.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except sqlite3.OperationalError as e:
            conn.rollback()
            if "database is locked" in str(e).lower():
                raise RuntimeError(
                    "The database is busy right now. Please wait a few seconds and try again."
                ) from e
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS bids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_name TEXT NOT NULL,
                    estimator TEXT NOT NULL,
                    original_bid_date TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    won_customer_id INTEGER REFERENCES customers(id),
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS bid_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bid_id INTEGER NOT NULL REFERENCES bids(id),
                    customer_id INTEGER NOT NULL REFERENCES customers(id)
                );

                CREATE TABLE IF NOT EXISTS bid_revisions (
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

                CREATE TABLE IF NOT EXISTS invoice_data (
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

                CREATE TABLE IF NOT EXISTS bid_moraware_links (
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

                CREATE TABLE IF NOT EXISTS bid_moraware_allocations (
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

                CREATE TABLE IF NOT EXISTS bid_board_items (
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
                );

                CREATE TABLE IF NOT EXISTS bid_board_item_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    customer_id INTEGER NOT NULL REFERENCES customers(id)
                );

                CREATE TABLE IF NOT EXISTS estimators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT,
                    active INTEGER DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS customer_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                    email TEXT NOT NULL,
                    name TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS bid_board_item_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    customer_contact_id INTEGER NOT NULL REFERENCES customer_contacts(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bid_board_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    label TEXT,
                    value TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS bid_board_item_bids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_item_id INTEGER NOT NULL REFERENCES bid_board_items(id) ON DELETE CASCADE,
                    bid_id INTEGER NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(board_item_id, bid_id)
                );
            """)

            new_columns = [
                ("bids", "salesperson", "TEXT"),
                ("bids", "project_manager", "TEXT"),
                ("bids", "moraware_job_date", "TEXT"),
                ("bids", "won_date", "TEXT"),
                ("bids", "won_notes", "TEXT"),
                ("bids", "moraware_job_id", "TEXT"),
                ("bids", "moraware_job_number", "TEXT"),
                ("bids", "moraware_job_status", "TEXT"),
                ("bids", "last_moraware_sync_at", "TEXT"),
                ("bids", "est_complete_date", "TEXT"),
                ("bids", "est_complete_date_manual", "INTEGER DEFAULT 0"),
                ("bids", "est_start_month", "TEXT"),
                ("bids", "moraware_created_date", "TEXT"),
                ("bids", "notebook_notes", "TEXT"),
                ("bids", "parent_bid_id", "INTEGER REFERENCES bids(id)"),
                ("bids", "bid_role", "TEXT DEFAULT 'normal'"),
                ("bids", "exclude_from_rollups", "INTEGER DEFAULT 0"),
                ("invoice_data", "sq_ft", "REAL"),
                ("invoice_data", "template_date", "TEXT"),
                ("invoice_data", "install_date", "TEXT"),
                ("invoice_data", "contact_customer_date", "TEXT"),
                ("invoice_data", "contact_customer_notes", "TEXT"),
                ("invoice_data", "moraware_job_id", "TEXT"),
                ("bid_moraware_links", "moraware_job_name", "TEXT"),
                ("bid_board_items", "location", "TEXT"),
                ("bid_board_items", "source", "TEXT DEFAULT 'LOCAL'"),
                ("bid_board_items", "outlook_event_id", "TEXT"),
                ("bid_board_items", "outlook_calendar_id", "TEXT"),
                ("bid_board_items", "outlook_last_modified", "TEXT"),
                ("bid_board_items", "outlook_last_synced", "TEXT"),
                ("bid_board_items", "outlook_source_notes", "TEXT"),
                ("bids", "due_date", "TEXT"),
                ("bids", "location", "TEXT"),
            ]
            for table, col, col_type in new_columns:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        continue
                    logger.exception("Schema migration failed while adding %s.%s", table, col)
                    raise

            conn.executescript("""
                CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status);
                CREATE INDEX IF NOT EXISTS idx_bids_moraware_job_id ON bids(moraware_job_id);
                CREATE INDEX IF NOT EXISTS idx_bids_moraware_job_status ON bids(moraware_job_status);
                CREATE INDEX IF NOT EXISTS idx_bids_original_bid_date ON bids(original_bid_date);
                CREATE INDEX IF NOT EXISTS idx_bids_parent_bid_id ON bids(parent_bid_id);
                CREATE INDEX IF NOT EXISTS idx_bids_bid_role ON bids(bid_role);
                CREATE INDEX IF NOT EXISTS idx_bids_exclude_rollups ON bids(exclude_from_rollups);
                CREATE INDEX IF NOT EXISTS idx_invoice_data_bid_id ON invoice_data(bid_id);
                CREATE INDEX IF NOT EXISTS idx_invoice_data_bid_job_phase ON invoice_data(bid_id, moraware_job_id, phase);
                CREATE INDEX IF NOT EXISTS idx_bid_revisions_bid_id_revision_no ON bid_revisions(bid_id, revision_no);
                CREATE INDEX IF NOT EXISTS idx_bid_moraware_links_bid_id ON bid_moraware_links(bid_id);
                CREATE INDEX IF NOT EXISTS idx_bid_moraware_links_job_id ON bid_moraware_links(moraware_job_id);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_bid_moraware_links_primary
                    ON bid_moraware_links(bid_id) WHERE is_primary = 1;
                CREATE INDEX IF NOT EXISTS idx_bid_moraware_allocations_bid_id ON bid_moraware_allocations(bid_id);
                CREATE INDEX IF NOT EXISTS idx_bid_board_items_board_date ON bid_board_items(board_date);
                CREATE INDEX IF NOT EXISTS idx_bid_board_items_board_status ON bid_board_items(board_status);
                CREATE INDEX IF NOT EXISTS idx_bid_board_items_estimator ON bid_board_items(estimator);
                CREATE INDEX IF NOT EXISTS idx_bid_board_item_customers_item ON bid_board_item_customers(board_item_id);
                CREATE INDEX IF NOT EXISTS idx_estimators_name ON estimators(name);
                CREATE INDEX IF NOT EXISTS idx_customer_contacts_customer ON customer_contacts(customer_id);
                CREATE INDEX IF NOT EXISTS idx_bid_board_item_contacts_item ON bid_board_item_contacts(board_item_id);
                CREATE INDEX IF NOT EXISTS idx_bid_board_attachments_item ON bid_board_attachments(board_item_id);
                CREATE INDEX IF NOT EXISTS idx_bid_board_item_bids_item ON bid_board_item_bids(board_item_id);
                CREATE INDEX IF NOT EXISTS idx_bid_board_item_bids_bid ON bid_board_item_bids(bid_id);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_board_outlook_event
                    ON bid_board_items(outlook_calendar_id, outlook_event_id)
                    WHERE outlook_event_id IS NOT NULL;
            """)

            conn.execute(
                """INSERT OR IGNORE INTO bid_board_item_bids (board_item_id, bid_id)
                   SELECT id, created_bid_id FROM bid_board_items
                   WHERE created_bid_id IS NOT NULL"""
            )

            self._seed_estimators_if_empty(conn)

            conn.execute(
                """
                INSERT OR IGNORE INTO bid_moraware_links (bid_id, moraware_job_id, moraware_job_number, is_primary)
                SELECT b.id,
                       TRIM(b.moraware_job_id),
                       NULLIF(TRIM(COALESCE(b.moraware_job_number, '')), ''),
                       1
                FROM bids b
                WHERE NULLIF(TRIM(COALESCE(b.moraware_job_id, '')), '') IS NOT NULL
                """
            )
            conn.execute(
                """
                UPDATE bid_moraware_links
                SET is_primary = CASE
                    WHEN id = (
                        SELECT l2.id
                        FROM bid_moraware_links l2
                        WHERE l2.bid_id = bid_moraware_links.bid_id
                        ORDER BY l2.is_primary DESC, l2.id ASC
                        LIMIT 1
                    ) THEN 1
                    ELSE 0
                END
                """
            )

            conn.execute(
                """
                WITH latest_rev AS (
                    SELECT br.bid_id,
                           COALESCE(br.bid_total, 0) AS bid_total,
                           COALESCE(br.solid_surf_sf, 0) AS solid_surf_sf,
                           COALESCE(br.stone_sf, 0) AS stone_sf
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions
                        GROUP BY bid_id
                    ) lr ON lr.bid_id = br.bid_id AND lr.max_rev = br.revision_no
                )
                INSERT OR IGNORE INTO bid_moraware_allocations
                    (bid_id, moraware_job_id, allocated_bid_total, allocated_solid_surf_sf, allocated_stone_sf)
                SELECT l.bid_id,
                       l.moraware_job_id,
                       COALESCE(r.bid_total, 0),
                       COALESCE(r.solid_surf_sf, 0),
                       COALESCE(r.stone_sf, 0)
                FROM bid_moraware_links l
                LEFT JOIN latest_rev r ON r.bid_id = l.bid_id
                WHERE l.is_primary = 1
                """
            )

            conn.execute(
                "UPDATE bids SET status='PENDING' WHERE status IN ('LOST', 'DEAD')"
            )
            conn.execute("UPDATE bids SET bid_role='normal' WHERE NULLIF(TRIM(COALESCE(bid_role,'')), '') IS NULL")
            conn.execute("UPDATE bids SET exclude_from_rollups=0 WHERE exclude_from_rollups IS NULL")
            conn.execute(
                """
                UPDATE bids
                SET won_date = moraware_created_date
                WHERE status = 'WON'
                  AND NULLIF(TRIM(COALESCE(won_date, '')), '') IS NULL
                  AND NULLIF(TRIM(COALESCE(moraware_job_id, '')), '') IS NOT NULL
                  AND NULLIF(TRIM(COALESCE(moraware_created_date, '')), '') IS NOT NULL
                """
            )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    def add_customer(self, name: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO customers (name) VALUES (?)", (name.strip(),)
            )
            return cur.lastrowid

    def get_customers(self, active_only=False, search=""):
        with self._conn() as conn:
            sql = "SELECT * FROM customers WHERE 1=1"
            params = []
            if active_only:
                sql += " AND active = 1"
            if search:
                sql += " AND name LIKE ?"
                params.append(f"%{search}%")
            sql += " ORDER BY name COLLATE NOCASE"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_customer_by_name(self, name: str):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM customers WHERE LOWER(name) = LOWER(?)",
                (name.strip(),),
            ).fetchone()
            return dict(row) if row else None

    def update_customer(self, customer_id: int, name: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE customers SET name = ? WHERE id = ?",
                (name.strip(), customer_id),
            )

    def toggle_customer_active(self, customer_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE customers SET active = CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id = ?",
                (customer_id,),
            )

    def get_customer_bid_count(self, customer_id: int) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT bid_id) as cnt FROM bid_customers WHERE customer_id = ?",
                (customer_id,),
            ).fetchone()
            return row["cnt"] if row else 0

    def merge_customers(self, merge_from_id: int, merge_into_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bid_customers SET customer_id = ? WHERE customer_id = ?",
                (merge_into_id, merge_from_id),
            )
            conn.execute("""
                DELETE FROM bid_customers WHERE id NOT IN (
                    SELECT MIN(id) FROM bid_customers GROUP BY bid_id, customer_id
                )
            """)
            conn.execute(
                "UPDATE bid_board_item_customers SET customer_id = ? WHERE customer_id = ?",
                (merge_into_id, merge_from_id),
            )
            conn.execute("""
                DELETE FROM bid_board_item_customers WHERE id NOT IN (
                    SELECT MIN(id) FROM bid_board_item_customers
                    GROUP BY board_item_id, customer_id
                )
            """)
            conn.execute(
                "UPDATE bids SET won_customer_id = ? WHERE won_customer_id = ?",
                (merge_into_id, merge_from_id),
            )
            # Reassign contacts; drop duplicates that already exist on the kept account
            into_emails = {
                (r["email"] or "").strip().lower()
                for r in conn.execute(
                    "SELECT email FROM customer_contacts WHERE customer_id = ?",
                    (merge_into_id,),
                ).fetchall()
            }
            from_contacts = conn.execute(
                "SELECT id, email FROM customer_contacts WHERE customer_id = ?",
                (merge_from_id,),
            ).fetchall()
            for fc in from_contacts:
                email_key = (fc["email"] or "").strip().lower()
                if email_key and email_key in into_emails:
                    into_row = conn.execute(
                        """SELECT id FROM customer_contacts
                           WHERE customer_id = ? AND LOWER(TRIM(email)) = ?
                           LIMIT 1""",
                        (merge_into_id, email_key),
                    ).fetchone()
                    if into_row:
                        conn.execute(
                            """UPDATE bid_board_item_contacts
                               SET customer_contact_id = ?
                               WHERE customer_contact_id = ?""",
                            (into_row["id"], fc["id"]),
                        )
                        conn.execute(
                            """DELETE FROM bid_board_item_contacts WHERE id NOT IN (
                                SELECT MIN(id) FROM bid_board_item_contacts
                                GROUP BY board_item_id, customer_contact_id
                            )"""
                        )
                    conn.execute("DELETE FROM customer_contacts WHERE id = ?", (fc["id"],))
                else:
                    conn.execute(
                        "UPDATE customer_contacts SET customer_id = ? WHERE id = ?",
                        (merge_into_id, fc["id"]),
                    )
                    if email_key:
                        into_emails.add(email_key)
            conn.execute(
                "DELETE FROM customers WHERE id = ?",
                (merge_from_id,),
            )

    # ------------------------------------------------------------------
    # Bids
    # ------------------------------------------------------------------
    def _insert_bid_rows(self, conn, bid_name: str, estimator: str, original_bid_date: str,
                         notes: str, customer_ids: list, bid_total: float,
                         solid_surf_sf: float = 0, stone_sf: float = 0,
                         due_date: str = None, location: str = None) -> int:
        """Insert a bid + its customer links + revision 1 using an existing connection.

        Shared by add_bid() and log_board_item_bid() so normal bid creation
        logic is never duplicated. Does not open/commit its own transaction.
        """
        due = (due_date or "").strip()[:10] or None
        loc = (location or "").strip() or None
        cur = conn.execute(
            """INSERT INTO bids (bid_name, estimator, original_bid_date, notes, due_date, location)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (bid_name.strip(), estimator.strip(), original_bid_date, notes, due, loc),
        )
        bid_id = cur.lastrowid

        for cid in customer_ids:
            conn.execute(
                "INSERT INTO bid_customers (bid_id, customer_id) VALUES (?, ?)",
                (bid_id, cid),
            )

        conn.execute(
            """INSERT INTO bid_revisions
               (bid_id, revision_no, revision_date, bid_total, solid_surf_sf, stone_sf)
               VALUES (?, 1, ?, ?, ?, ?)""",
            (bid_id, original_bid_date, bid_total, solid_surf_sf, stone_sf),
        )
        return bid_id

    def add_bid(self, bid_name: str, estimator: str, original_bid_date: str,
                notes: str, customer_ids: list, bid_total: float,
                solid_surf_sf: float = 0, stone_sf: float = 0,
                due_date: str = None, location: str = None) -> int:
        with self._conn() as conn:
            return self._insert_bid_rows(
                conn, bid_name, estimator, original_bid_date, notes,
                customer_ids, bid_total, solid_surf_sf, stone_sf,
                due_date=due_date, location=location,
            )

    def get_bids(self, search="", estimator="", status="", year=""):
        """Return list of bid dicts with latest revision data and customer names."""
        with self._conn() as conn:
            sql = """
                SELECT b.*,
                       r.bid_total, r.solid_surf_sf, r.stone_sf, r.revision_no,
                       GROUP_CONCAT(c.name, ', ') AS customer_names
                FROM bids b
                LEFT JOIN (
                    SELECT br.*
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                LEFT JOIN bid_customers bc ON bc.bid_id = b.id
                LEFT JOIN customers c ON c.id = bc.customer_id
                WHERE 1=1
                  AND COALESCE(b.bid_role, 'normal') != 'parent'
            """
            params = []

            if search:
                sql += " AND (b.bid_name LIKE ? OR c.name LIKE ?)"
                params += [f"%{search}%", f"%{search}%"]
            if estimator:
                sql += " AND b.estimator = ?"
                params.append(estimator)
            if status:
                sql += " AND b.status = ?"
                params.append(status)
            if year:
                sql += " AND strftime('%Y', b.original_bid_date) = ?"
                params.append(str(year))

            sql += " GROUP BY b.id ORDER BY b.original_bid_date ASC, b.id ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_bid_by_id(self, bid_id: int):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM bids WHERE id = ?", (bid_id,)).fetchone()
            return dict(row) if row else None

    def update_bid(self, bid_id: int, bid_name: str, estimator: str,
                   original_bid_date: str, notes: str, customer_ids: list,
                   due_date: str = None, location: str = None):
        due = (due_date or "").strip()[:10] or None
        loc = (location or "").strip() or None
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET bid_name=?, estimator=?, original_bid_date=?, notes=?,
                       due_date=?, location=?
                   WHERE id=?""",
                (bid_name.strip(), estimator.strip(), original_bid_date, notes, due, loc, bid_id),
            )
            conn.execute("DELETE FROM bid_customers WHERE bid_id=?", (bid_id,))
            for cid in customer_ids:
                conn.execute(
                    "INSERT INTO bid_customers (bid_id, customer_id) VALUES (?, ?)",
                    (bid_id, cid),
                )

    def delete_bid(self, bid_id: int):
        with self._conn() as conn:
            bid = conn.execute("SELECT status FROM bids WHERE id=?", (bid_id,)).fetchone()
            if bid and bid["status"] == "WON":
                raise ValueError("Cannot delete a WON bid.")
            conn.execute("DELETE FROM bid_revisions WHERE bid_id=?", (bid_id,))
            conn.execute("DELETE FROM bid_customers WHERE bid_id=?", (bid_id,))
            conn.execute("DELETE FROM bids WHERE id=?", (bid_id,))

    def mark_bid_status(self, bid_id: int, status: str, won_customer_id: int = None):
        with self._conn() as conn:
            if status == "WON" and won_customer_id:
                conn.execute(
                    "UPDATE bids SET status=?, won_customer_id=? WHERE id=?",
                    (status, won_customer_id, bid_id),
                )
            else:
                conn.execute(
                    "UPDATE bids SET status=?, won_customer_id=NULL WHERE id=?",
                    (status, bid_id),
                )

    # ------------------------------------------------------------------
    # Bid-Customer links
    # ------------------------------------------------------------------
    def get_bid_customers(self, bid_id: int):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT c.* FROM customers c
                       JOIN bid_customers bc ON bc.customer_id = c.id
                       WHERE bc.bid_id = ?
                       ORDER BY c.name COLLATE NOCASE""",
                    (bid_id,),
                ).fetchall()
            ]

    # ------------------------------------------------------------------
    # Revisions
    # ------------------------------------------------------------------
    def add_revision(self, bid_id: int, revision_date: str, bid_total: float,
                     solid_surf_sf: float = 0, stone_sf: float = 0, reason: str = ""):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(revision_no), 0) + 1 AS next_rev FROM bid_revisions WHERE bid_id=?",
                (bid_id,),
            ).fetchone()
            next_rev = row["next_rev"]
            conn.execute(
                """INSERT INTO bid_revisions
                   (bid_id, revision_no, revision_date, bid_total, solid_surf_sf, stone_sf, reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (bid_id, next_rev, revision_date, bid_total, solid_surf_sf, stone_sf, reason),
            )
            return next_rev

    def get_revisions(self, bid_id: int):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM bid_revisions WHERE bid_id=? ORDER BY revision_no DESC",
                    (bid_id,),
                ).fetchall()
            ]

    def get_latest_revision(self, bid_id: int):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM bid_revisions WHERE bid_id=? ORDER BY revision_no DESC LIMIT 1",
                (bid_id,),
            ).fetchone()
            return dict(row) if row else None

    def update_revision(self, revision_id: int, revision_date: str, bid_total: float,
                        solid_surf_sf: float = 0, stone_sf: float = 0, reason: str = ""):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bid_revisions
                   SET revision_date=?, bid_total=?, solid_surf_sf=?, stone_sf=?, reason=?
                   WHERE id=?""",
                (revision_date, bid_total, solid_surf_sf, stone_sf, reason, revision_id),
            )

    # ------------------------------------------------------------------
    # Stats & Reports
    # ------------------------------------------------------------------
    def get_stats(self):
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) as cnt FROM bids").fetchone()["cnt"]
            active = conn.execute(
                "SELECT COUNT(*) as cnt FROM bids WHERE status='PENDING'"
            ).fetchone()["cnt"]
            won = conn.execute(
                "SELECT COUNT(*) as cnt FROM bids WHERE status='WON'"
            ).fetchone()["cnt"]

            value_row = conn.execute("""
                SELECT COALESCE(SUM(r.bid_total), 0) AS total_value
                FROM bids b
                JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
            """).fetchone()
            total_value = value_row["total_value"] if value_row else 0

            return {
                "total": total,
                "active": active,
                "won": won,
                "total_value": total_value,
            }

    def get_estimators(self):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT estimator FROM bids ORDER BY estimator COLLATE NOCASE"
            ).fetchall()
            return [r["estimator"] for r in rows]

    def get_all_estimator_names(self):
        """Union of roster + historical bid + board-item estimator names."""
        names = set()
        for e in self.get_estimators():
            if e and str(e).strip():
                names.add(str(e).strip())
        for e in self.get_board_estimators():
            if e and str(e).strip():
                names.add(str(e).strip())
        for row in self.get_estimators_roster(active_only=False):
            if row.get("name"):
                names.add(row["name"].strip())
        return sorted(names, key=lambda s: s.lower())

    # ------------------------------------------------------------------
    # Estimator roster (shared colors)
    # ------------------------------------------------------------------
    def _seed_estimators_if_empty(self, conn):
        """One-time seed from distinct bid estimator names when roster is empty."""
        count = conn.execute("SELECT COUNT(*) AS cnt FROM estimators").fetchone()["cnt"]
        if count:
            return
        try:
            from config import get_estimator_colors, _auto_color_for
            overrides = get_estimator_colors()
        except Exception:
            overrides = {}

            def _auto_color_for(name):
                palette = [
                    "#4caf50", "#ff9800", "#e91e63", "#9c27b0", "#00bcd4",
                    "#ffc107", "#8bc34a", "#ff5722", "#795548", "#607d8b",
                ]
                if not name:
                    return "#6b6b6b"
                return palette[sum(ord(ch) for ch in name) % len(palette)]

        rows = conn.execute(
            """SELECT DISTINCT estimator FROM bids
               WHERE estimator IS NOT NULL AND TRIM(estimator) != ''
               ORDER BY estimator COLLATE NOCASE"""
        ).fetchall()
        for i, row in enumerate(rows):
            name = (row["estimator"] or "").strip()
            if not name:
                continue
            color = overrides.get(name) or _auto_color_for(name)
            conn.execute(
                "INSERT OR IGNORE INTO estimators (name, color, active, sort_order) VALUES (?, ?, 1, ?)",
                (name, color, i),
            )

    def get_estimators_roster(self, active_only=False):
        with self._conn() as conn:
            sql = "SELECT * FROM estimators WHERE 1=1"
            if active_only:
                sql += " AND active = 1"
            sql += " ORDER BY sort_order ASC, name COLLATE NOCASE"
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def get_estimator_color_map(self):
        """{name: hex_color} from the shared roster."""
        return {
            r["name"]: r["color"]
            for r in self.get_estimators_roster(active_only=False)
            if r.get("name") and r.get("color")
        }

    def add_estimator(self, name: str, color: str = None):
        name = (name or "").strip()
        if not name:
            raise ValueError("Estimator name is required.")
        if not color:
            from config import _auto_color_for
            color = _auto_color_for(name)
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id FROM estimators WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()
            if existing:
                raise ValueError(f"Estimator '{name}' already exists.")
            row = conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS nxt FROM estimators").fetchone()
            cur = conn.execute(
                "INSERT INTO estimators (name, color, active, sort_order) VALUES (?, ?, 1, ?)",
                (name, color, row["nxt"]),
            )
            return cur.lastrowid

    def update_estimator(self, estimator_id: int, name: str = None, color: str = None, active=None):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM estimators WHERE id = ?", (estimator_id,)).fetchone()
            if not row:
                raise ValueError("Estimator not found.")
            new_name = (name if name is not None else row["name"]).strip()
            new_color = color if color is not None else row["color"]
            new_active = row["active"] if active is None else (1 if active else 0)
            if not new_name:
                raise ValueError("Estimator name is required.")
            dup = conn.execute(
                "SELECT id FROM estimators WHERE LOWER(name) = LOWER(?) AND id != ?",
                (new_name, estimator_id),
            ).fetchone()
            if dup:
                raise ValueError(f"Estimator '{new_name}' already exists.")
            conn.execute(
                "UPDATE estimators SET name=?, color=?, active=? WHERE id=?",
                (new_name, new_color, new_active, estimator_id),
            )

    def delete_estimator(self, estimator_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM estimators WHERE id = ?", (estimator_id,))

    def pull_estimators_from_bids(self):
        """Insert any bid/board estimator names missing from the roster. Returns count added."""
        from config import get_estimator_colors, _auto_color_for
        overrides = get_estimator_colors()
        names = set()
        for e in self.get_estimators():
            if e and str(e).strip():
                names.add(str(e).strip())
        for e in self.get_board_estimators():
            if e and str(e).strip():
                names.add(str(e).strip())
        added = 0
        with self._conn() as conn:
            existing = {
                (r["name"] or "").strip().lower()
                for r in conn.execute("SELECT name FROM estimators").fetchall()
            }
            row = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS mx FROM estimators").fetchone()
            nxt = row["mx"] + 1
            for name in sorted(names, key=lambda s: s.lower()):
                if name.lower() in existing:
                    continue
                color = overrides.get(name) or _auto_color_for(name)
                conn.execute(
                    "INSERT OR IGNORE INTO estimators (name, color, active, sort_order) VALUES (?, ?, 1, ?)",
                    (name, color, nxt),
                )
                nxt += 1
                added += 1
        return added

    # ------------------------------------------------------------------
    # Customer contacts (account emails)
    # ------------------------------------------------------------------
    def get_customer_contacts(self, customer_id: int, active_only=False):
        with self._conn() as conn:
            sql = "SELECT * FROM customer_contacts WHERE customer_id = ?"
            params = [customer_id]
            if active_only:
                sql += " AND active = 1"
            sql += " ORDER BY name COLLATE NOCASE, email COLLATE NOCASE"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def add_customer_contact(self, customer_id: int, email: str, name: str = ""):
        email = (email or "").strip()
        name = (name or "").strip()
        if not email:
            raise ValueError("Email is required.")
        with self._conn() as conn:
            existing = conn.execute(
                """SELECT id FROM customer_contacts
                   WHERE customer_id = ? AND LOWER(TRIM(email)) = LOWER(?)""",
                (customer_id, email),
            ).fetchone()
            if existing:
                return existing["id"]
            cur = conn.execute(
                "INSERT INTO customer_contacts (customer_id, email, name, active) VALUES (?, ?, ?, 1)",
                (customer_id, email, name or None),
            )
            return cur.lastrowid

    def update_customer_contact(self, contact_id: int, email: str, name: str = "", active=None):
        email = (email or "").strip()
        name = (name or "").strip()
        if not email:
            raise ValueError("Email is required.")
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM customer_contacts WHERE id = ?", (contact_id,)).fetchone()
            if not row:
                raise ValueError("Contact not found.")
            new_active = row["active"] if active is None else (1 if active else 0)
            conn.execute(
                "UPDATE customer_contacts SET email=?, name=?, active=? WHERE id=?",
                (email, name or None, new_active, contact_id),
            )

    def delete_customer_contact(self, contact_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM customer_contacts WHERE id = ?", (contact_id,))

    def get_board_item_contacts(self, item_id: int):
        """Recipients chosen for a board item, with company + email + name."""
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT cc.id, cc.email, cc.name, cc.customer_id, c.name AS company_name
                       FROM bid_board_item_contacts bic
                       JOIN customer_contacts cc ON cc.id = bic.customer_contact_id
                       JOIN customers c ON c.id = cc.customer_id
                       WHERE bic.board_item_id = ?
                       ORDER BY c.name COLLATE NOCASE, cc.name COLLATE NOCASE, cc.email COLLATE NOCASE""",
                    (item_id,),
                ).fetchall()
            ]

    def set_board_item_contacts(self, item_id: int, contact_ids: list):
        contact_ids = list(dict.fromkeys(int(cid) for cid in (contact_ids or [])))
        with self._conn() as conn:
            conn.execute("DELETE FROM bid_board_item_contacts WHERE board_item_id = ?", (item_id,))
            for cid in contact_ids:
                conn.execute(
                    "INSERT INTO bid_board_item_contacts (board_item_id, customer_contact_id) VALUES (?, ?)",
                    (item_id, cid),
                )

    # ------------------------------------------------------------------
    # Bid Board attachments / links
    # ------------------------------------------------------------------
    def add_board_attachment(self, item_id: int, kind: str, label: str, value: str) -> int:
        kind = (kind or "").strip().lower()
        if kind not in ("file", "link"):
            raise ValueError("Attachment kind must be 'file' or 'link'.")
        value = (value or "").strip()
        if not value:
            raise ValueError("Attachment value is required.")
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO bid_board_attachments (board_item_id, kind, label, value)
                   VALUES (?, ?, ?, ?)""",
                (item_id, kind, (label or "").strip() or None, value),
            )
            return cur.lastrowid

    def get_board_attachments(self, item_id: int):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT * FROM bid_board_attachments
                       WHERE board_item_id = ? ORDER BY id ASC""",
                    (item_id,),
                ).fetchall()
            ]

    def delete_board_attachment(self, attachment_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM bid_board_attachments WHERE id = ?", (attachment_id,))

    # ------------------------------------------------------------------
    # Bid Board (Calendar) - separate from normal bids
    # ------------------------------------------------------------------
    UNASSIGNED = "__UNASSIGNED__"

    @staticmethod
    def _norm_estimator(estimator):
        """Normalize an estimator value to a stripped name or None (unassigned)."""
        if estimator is None:
            return None
        estimator = str(estimator).strip()
        return estimator or None

    def add_board_item(self, bid_name: str, board_date: str, actual_due_date=None,
                       actual_due_time=None, estimator=None, notes: str = "",
                       customer_ids: list = None, location: str = None) -> int:
        """Create a new Bid Board item. Defaults to IN_PROGRESS / Unassigned."""
        customer_ids = customer_ids or []
        loc = (location or "").strip() or None
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO bid_board_items
                   (bid_name, board_date, actual_due_date, actual_due_time,
                    estimator, board_status, notes, location)
                   VALUES (?, ?, ?, ?, ?, 'IN_PROGRESS', ?, ?)""",
                (bid_name.strip(), board_date, actual_due_date or None,
                 actual_due_time or None, self._norm_estimator(estimator), notes or "", loc),
            )
            item_id = cur.lastrowid
            for cid in customer_ids:
                conn.execute(
                    "INSERT INTO bid_board_item_customers (board_item_id, customer_id) VALUES (?, ?)",
                    (item_id, cid),
                )
            return item_id

    def update_board_item(self, item_id: int, bid_name: str, board_date: str,
                         actual_due_date=None, actual_due_time=None, estimator=None,
                         notes: str = "", customer_ids: list = None, location: str = None):
        """Update editable fields of a board item. Does NOT touch board_status,
        completed_at, or created_bid_id (status changes go through their own paths)."""
        customer_ids = customer_ids or []
        loc = (location or "").strip() or None
        with self._conn() as conn:
            conn.execute(
                """UPDATE bid_board_items
                   SET bid_name=?, board_date=?, actual_due_date=?, actual_due_time=?,
                       estimator=?, notes=?, location=?, updated_at=datetime('now')
                   WHERE id=?""",
                (bid_name.strip(), board_date, actual_due_date or None,
                 actual_due_time or None, self._norm_estimator(estimator),
                 notes or "", loc, item_id),
            )
            conn.execute("DELETE FROM bid_board_item_customers WHERE board_item_id=?", (item_id,))
            for cid in customer_ids:
                conn.execute(
                    "INSERT INTO bid_board_item_customers (board_item_id, customer_id) VALUES (?, ?)",
                    (item_id, cid),
                )

    def update_board_item_date(self, item_id: int, board_date: str):
        """Drag-and-drop: move a card to a new Board Date only. Never touches
        actual_due_date, status, the linked bid, or Moraware."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE bid_board_items SET board_date=?, updated_at=datetime('now') WHERE id=?",
                (board_date, item_id),
            )

    def assign_board_item(self, item_id: int, estimator=None):
        """Assign/unassign the estimator on a board item (assignment only)."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE bid_board_items SET estimator=?, updated_at=datetime('now') WHERE id=?",
                (self._norm_estimator(estimator), item_id),
            )

    def set_board_item_status(self, item_id: int, status: str):
        """Set IN_PROGRESS or NOT_BIDDING. COMPLETE uses mark_board_item_complete()."""
        if status not in ("IN_PROGRESS", "NOT_BIDDING"):
            raise ValueError(
                "Board status can only be set to IN_PROGRESS or NOT_BIDDING here; "
                "COMPLETE uses mark_board_item_complete()."
            )
        extra = ", completed_at=NULL" if status == "IN_PROGRESS" else ""
        with self._conn() as conn:
            conn.execute(
                f"""UPDATE bid_board_items
                    SET board_status=?, updated_at=datetime('now'){extra}
                    WHERE id=?""",
                (status, item_id),
            )

    def get_board_item(self, item_id: int):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT bbi.*, GROUP_CONCAT(c.name, ', ') AS customer_names,
                          (SELECT COUNT(*) FROM bid_board_attachments a
                           WHERE a.board_item_id = bbi.id) AS attachment_count,
                          (SELECT COUNT(*) FROM bid_board_item_contacts rc
                           WHERE rc.board_item_id = bbi.id) AS recipient_count,
                          (SELECT COUNT(*) FROM bid_board_item_bids lb
                           WHERE lb.board_item_id = bbi.id) AS linked_bid_count
                   FROM bid_board_items bbi
                   LEFT JOIN bid_board_item_customers bic ON bic.board_item_id = bbi.id
                   LEFT JOIN customers c ON c.id = bic.customer_id
                   WHERE bbi.id = ?
                   GROUP BY bbi.id""",
                (item_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_board_item_customers(self, item_id: int):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT c.* FROM customers c
                       JOIN bid_board_item_customers bic ON bic.customer_id = c.id
                       WHERE bic.board_item_id = ?
                       ORDER BY c.name COLLATE NOCASE""",
                    (item_id,),
                ).fetchall()
            ]

    def get_board_items(self, start_date: str, end_date: str,
                       estimator=None, statuses=None):
        """Return board items whose board_date falls in [start_date, end_date].

        estimator: None = all; Database.UNASSIGNED = estimator IS NULL; else exact name.
        statuses:  None = all; otherwise a list of board_status values to include.
        """
        with self._conn() as conn:
            sql = """
                SELECT bbi.*, GROUP_CONCAT(c.name, ', ') AS customer_names,
                       (SELECT COUNT(*) FROM bid_board_attachments a
                        WHERE a.board_item_id = bbi.id) AS attachment_count,
                       (SELECT COUNT(*) FROM bid_board_item_contacts rc
                        WHERE rc.board_item_id = bbi.id) AS recipient_count,
                       (SELECT COUNT(*) FROM bid_board_item_bids lb
                        WHERE lb.board_item_id = bbi.id) AS linked_bid_count
                FROM bid_board_items bbi
                LEFT JOIN bid_board_item_customers bic ON bic.board_item_id = bbi.id
                LEFT JOIN customers c ON c.id = bic.customer_id
                WHERE bbi.board_date >= ? AND bbi.board_date <= ?
            """
            params = [start_date, end_date]

            if estimator == self.UNASSIGNED:
                sql += " AND bbi.estimator IS NULL"
            elif estimator:
                sql += " AND bbi.estimator = ?"
                params.append(estimator)

            if statuses:
                placeholders = ", ".join("?" for _ in statuses)
                sql += f" AND bbi.board_status IN ({placeholders})"
                params.extend(statuses)

            sql += " GROUP BY bbi.id ORDER BY bbi.board_date ASC, bbi.id ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def search_board_items(self, query: str, limit: int = 80, *, quick: bool = False):
        """Find board items by name/account/estimator/notes/location (includes COMPLETE).

        quick=True skips notes/source-notes (faster typeahead; still matches name/account/etc.).
        """
        q = (query or "").strip()
        if not q:
            return []
        like = f"%{q}%"
        if quick:
            sql = """SELECT bbi.id, bbi.bid_name, bbi.board_date, bbi.estimator,
                            bbi.board_status, bbi.location,
                            GROUP_CONCAT(c.name, ', ') AS customer_names
                     FROM bid_board_items bbi
                     LEFT JOIN bid_board_item_customers bic ON bic.board_item_id = bbi.id
                     LEFT JOIN customers c ON c.id = bic.customer_id
                     WHERE bbi.bid_name LIKE ?
                        OR IFNULL(bbi.estimator, '') LIKE ?
                        OR IFNULL(bbi.location, '') LIKE ?
                        OR IFNULL(c.name, '') LIKE ?
                     GROUP BY bbi.id
                     ORDER BY bbi.board_date DESC, bbi.id DESC
                     LIMIT ?"""
            params = (like, like, like, like, int(limit))
        else:
            sql = """SELECT bbi.*, GROUP_CONCAT(c.name, ', ') AS customer_names,
                              (SELECT COUNT(*) FROM bid_board_item_bids lb
                               WHERE lb.board_item_id = bbi.id) AS linked_bid_count
                       FROM bid_board_items bbi
                       LEFT JOIN bid_board_item_customers bic ON bic.board_item_id = bbi.id
                       LEFT JOIN customers c ON c.id = bic.customer_id
                       WHERE bbi.bid_name LIKE ?
                          OR IFNULL(bbi.estimator, '') LIKE ?
                          OR IFNULL(bbi.notes, '') LIKE ?
                          OR IFNULL(bbi.outlook_source_notes, '') LIKE ?
                          OR IFNULL(bbi.location, '') LIKE ?
                          OR IFNULL(c.name, '') LIKE ?
                       GROUP BY bbi.id
                       ORDER BY bbi.board_date DESC, bbi.id DESC
                       LIMIT ?"""
            params = (like, like, like, like, like, like, int(limit))
        with self._conn() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def count_board_items_by_estimator(self, start_date: str, end_date: str, statuses=None):
        """Return {estimator_or_Unassigned: count} for the board_date window."""
        with self._conn() as conn:
            sql = """
                SELECT CASE
                         WHEN estimator IS NULL OR TRIM(estimator) = '' THEN 'Unassigned'
                         ELSE estimator
                       END AS est_key,
                       COUNT(*) AS cnt
                FROM bid_board_items
                WHERE board_date >= ? AND board_date <= ?
            """
            params = [start_date, end_date]
            if statuses:
                placeholders = ", ".join("?" for _ in statuses)
                sql += f" AND board_status IN ({placeholders})"
                params.extend(statuses)
            sql += " GROUP BY est_key ORDER BY cnt DESC, est_key COLLATE NOCASE"
            return [(r["est_key"], int(r["cnt"])) for r in conn.execute(sql, params).fetchall()]

    def get_board_estimators(self):
        """Distinct non-null estimators currently used on board items."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT DISTINCT estimator FROM bid_board_items
                   WHERE estimator IS NOT NULL AND TRIM(estimator) != ''
                   ORDER BY estimator COLLATE NOCASE"""
            ).fetchall()
            return [r["estimator"] for r in rows]

    def get_board_item_bids(self, item_id: int):
        """Normal BidTracker bids linked to a board opportunity (not revisions)."""
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT b.*,
                              r.bid_total, r.solid_surf_sf, r.stone_sf, r.revision_no,
                              GROUP_CONCAT(c.name, ', ') AS customer_names,
                              lb.created_at AS linked_at
                       FROM bid_board_item_bids lb
                       JOIN bids b ON b.id = lb.bid_id
                       LEFT JOIN (
                           SELECT br.*
                           FROM bid_revisions br
                           INNER JOIN (
                               SELECT bid_id, MAX(revision_no) AS max_rev
                               FROM bid_revisions GROUP BY bid_id
                           ) latest ON br.bid_id = latest.bid_id
                                   AND br.revision_no = latest.max_rev
                       ) r ON r.bid_id = b.id
                       LEFT JOIN bid_customers bc ON bc.bid_id = b.id
                       LEFT JOIN customers c ON c.id = bc.customer_id
                       WHERE lb.board_item_id = ?
                       GROUP BY b.id
                       ORDER BY lb.id ASC""",
                    (item_id,),
                ).fetchall()
            ]

    def log_board_item_bid(self, item_id: int, bid_name: str, estimator: str,
                           original_bid_date: str, notes: str, customer_ids: list,
                           bid_total: float, solid_surf_sf: float = 0,
                           stone_sf: float = 0, due_date: str = None,
                           location: str = None) -> int:
        """Create one normal bid and link it to the board item in one transaction.

        Does not mark the board item COMPLETE. A second call creates a second bid.
        Partial failure rolls back so a retry cannot leave an unlinked orphan bid.
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id FROM bid_board_items WHERE id = ?", (item_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Bid Board item {item_id} not found.")
            bid_id = self._insert_bid_rows(
                conn, bid_name, estimator, original_bid_date, notes,
                customer_ids, bid_total, solid_surf_sf, stone_sf,
                due_date=due_date, location=location,
            )
            conn.execute(
                """INSERT INTO bid_board_item_bids (board_item_id, bid_id)
                   VALUES (?, ?)""",
                (item_id, bid_id),
            )
            return bid_id

    def link_existing_board_bid(self, item_id: int, bid_id: int) -> int:
        """Attach an existing normal bid to a board item. Does not change board status."""
        item_id = int(item_id)
        bid_id = int(bid_id)
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id FROM bid_board_items WHERE id = ?", (item_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Bid Board item {item_id} not found.")
            bid = conn.execute("SELECT id FROM bids WHERE id = ?", (bid_id,)).fetchone()
            if bid is None:
                raise ValueError(f"Bid {bid_id} was not found.")
            existing = conn.execute(
                """SELECT id FROM bid_board_item_bids
                   WHERE board_item_id = ? AND bid_id = ?""",
                (item_id, bid_id),
            ).fetchone()
            if existing:
                return bid_id
            conn.execute(
                """INSERT INTO bid_board_item_bids (board_item_id, bid_id)
                   VALUES (?, ?)""",
                (item_id, bid_id),
            )
            return bid_id

    def unlink_board_item_bid(self, item_id: int, bid_id: int):
        """Remove the join only. Does not delete the normal bid or change board status."""
        with self._conn() as conn:
            conn.execute(
                """DELETE FROM bid_board_item_bids
                   WHERE board_item_id = ? AND bid_id = ?""",
                (int(item_id), int(bid_id)),
            )

    def find_bids_for_board_link(self, item_id: int, search: str = "", near_date: str = None):
        """Bids not yet linked to this card, nearby original_bid_date first."""
        from datetime import date as date_cls

        linked_ids = {int(b["id"]) for b in self.get_board_item_bids(item_id) if b.get("id")}
        rows = [r for r in self.get_bids(search=search or "") if int(r.get("id") or 0) not in linked_ids]
        near = None
        raw_near = (near_date or "")[:10]
        if len(raw_near) == 10:
            try:
                near = date_cls.fromisoformat(raw_near)
            except ValueError:
                near = None

        def _score(r):
            raw = (r.get("original_bid_date") or "")[:10]
            try:
                d = date_cls.fromisoformat(raw)
            except ValueError:
                return (1, 99999, (r.get("bid_name") or "").lower())
            delta = abs((d - near).days) if near else 99999
            return (0, delta, (r.get("bid_name") or "").lower())

        rows.sort(key=_score)
        return rows

    def get_board_item_by_outlook_event(self, calendar_id: str, event_id: str):
        calendar_id = (calendar_id or "").strip()
        event_id = (event_id or "").strip()
        if not calendar_id or not event_id:
            return None
        with self._conn() as conn:
            row = conn.execute(
                """SELECT bbi.*,
                          (SELECT COUNT(*) FROM bid_board_item_bids lb
                           WHERE lb.board_item_id = bbi.id) AS linked_bid_count
                   FROM bid_board_items bbi
                   WHERE bbi.outlook_calendar_id = ? AND bbi.outlook_event_id = ?""",
                (calendar_id, event_id),
            ).fetchone()
            return dict(row) if row else None

    def upsert_outlook_board_item(
        self,
        calendar_id: str,
        event_id: str,
        bid_name: str,
        board_date: str,
        estimator=None,
        board_status: str = "IN_PROGRESS",
        location: str = None,
        source_notes: str = None,
        last_modified: str = None,
    ) -> tuple:
        """Insert or update an Outlook-sourced board item.

        Updates only Outlook-managed fields. Returns (item_id, created_bool).
        """
        calendar_id = (calendar_id or "").strip()
        event_id = (event_id or "").strip()
        if not calendar_id or not event_id:
            raise ValueError("Outlook calendar id and event id are required.")
        bid_name = (bid_name or "").strip() or "(No subject)"
        if board_status not in ("IN_PROGRESS", "COMPLETE", "NOT_BIDDING"):
            board_status = "IN_PROGRESS"
        loc = (location or "").strip() or None
        notes = (source_notes or "").strip() or None
        estimator = self._norm_estimator(estimator)
        existing = self.get_board_item_by_outlook_event(calendar_id, event_id)
        with self._conn() as conn:
            if existing:
                completed_sql = ""
                if board_status == "COMPLETE" and existing.get("board_status") != "COMPLETE":
                    completed_sql = ", completed_at=COALESCE(completed_at, datetime('now'))"
                conn.execute(
                    f"""UPDATE bid_board_items
                        SET bid_name=?, board_date=?, estimator=?, board_status=?,
                            location=?, outlook_source_notes=?,
                            outlook_last_modified=?, outlook_last_synced=datetime('now'),
                            source='OUTLOOK', updated_at=datetime('now')
                            {completed_sql}
                        WHERE id=?""",
                    (
                        bid_name, board_date, estimator, board_status, loc, notes,
                        last_modified or None, existing["id"],
                    ),
                )
                return existing["id"], False
            if board_status == "COMPLETE":
                cur = conn.execute(
                    """INSERT INTO bid_board_items
                       (bid_name, board_date, estimator, board_status, notes, location,
                        source, outlook_event_id, outlook_calendar_id,
                        outlook_last_modified, outlook_last_synced, outlook_source_notes,
                        completed_at)
                       VALUES (?, ?, ?, ?, '', ?, 'OUTLOOK', ?, ?, ?, datetime('now'), ?,
                               datetime('now'))""",
                    (
                        bid_name, board_date, estimator, board_status, loc,
                        event_id, calendar_id, last_modified or None, notes,
                    ),
                )
            else:
                cur = conn.execute(
                    """INSERT INTO bid_board_items
                       (bid_name, board_date, estimator, board_status, notes, location,
                        source, outlook_event_id, outlook_calendar_id,
                        outlook_last_modified, outlook_last_synced, outlook_source_notes)
                       VALUES (?, ?, ?, ?, '', ?, 'OUTLOOK', ?, ?, ?, datetime('now'), ?)""",
                    (
                        bid_name, board_date, estimator, board_status, loc,
                        event_id, calendar_id, last_modified or None, notes,
                    ),
                )
            return cur.lastrowid, True

    def apply_board_item_outlook_hints(
        self, item_id: int, actual_due_date: str = None, customer_ids: list = None
    ) -> dict:
        """Fill empty Actual Due Date / Accounts only. Never overwrite existing values."""
        item_id = int(item_id)
        applied = {"due_date": False, "customers": 0}
        due = (actual_due_date or "").strip()[:10] or None
        if due and len(due) != 10:
            due = None
        ids = []
        for cid in customer_ids or []:
            try:
                ids.append(int(cid))
            except (TypeError, ValueError):
                pass
        ids = list(dict.fromkeys(ids))
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, actual_due_date FROM bid_board_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Bid Board item {item_id} not found.")
            if due and not (row["actual_due_date"] or "").strip():
                conn.execute(
                    """UPDATE bid_board_items
                       SET actual_due_date=?, updated_at=datetime('now')
                       WHERE id=?""",
                    (due, item_id),
                )
                applied["due_date"] = True
            if ids:
                existing = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM bid_board_item_customers WHERE board_item_id=?",
                    (item_id,),
                ).fetchone()
                if int(existing["cnt"] or 0) == 0:
                    for cid in ids:
                        ok = conn.execute(
                            "SELECT id FROM customers WHERE id = ?", (cid,)
                        ).fetchone()
                        if not ok:
                            continue
                        conn.execute(
                            """INSERT INTO bid_board_item_customers
                               (board_item_id, customer_id) VALUES (?, ?)""",
                            (item_id, cid),
                        )
                        applied["customers"] += 1
        return applied

    def get_customer_email_index(self):
        """Map lowercase email -> customer_id for Outlook body matching."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT LOWER(TRIM(email)) AS email, customer_id
                   FROM customer_contacts
                   WHERE email IS NOT NULL AND TRIM(email) != ''
                     AND COALESCE(active, 1) = 1"""
            ).fetchall()
            return {r["email"]: r["customer_id"] for r in rows if r["email"]}

    def mark_board_item_complete(self, item_id: int):
        """Mark a board opportunity COMPLETE. Does not create bids."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, board_status FROM bid_board_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Bid Board item {item_id} not found.")
            if row["board_status"] == "COMPLETE":
                return
            conn.execute(
                """UPDATE bid_board_items
                   SET board_status='COMPLETE',
                       completed_at=COALESCE(completed_at, datetime('now')),
                       updated_at=datetime('now')
                   WHERE id=?""",
                (item_id,),
            )

    def get_years(self):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT strftime('%Y', original_bid_date) AS yr FROM bids ORDER BY yr"
            ).fetchall()
            return [r["yr"] for r in rows if r["yr"]]

    def get_bids_by_status_summary(self, date_from="", date_to="", estimator=""):
        with self._conn() as conn:
            sql = """
                SELECT b.status, COUNT(*) as cnt,
                       COALESCE(SUM(r.bid_total), 0) as total_value
                FROM bids b
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE 1=1
            """
            params = []
            if date_from:
                sql += " AND b.original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND b.original_bid_date <= ?"
                params.append(date_to)
            if estimator:
                sql += " AND b.estimator = ?"
                params.append(estimator)
            sql += " GROUP BY b.status"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_bids_by_customer(self, date_from="", date_to="", estimator="", status=""):
        with self._conn() as conn:
            sql = """
                SELECT c.name AS customer_name,
                       COUNT(DISTINCT b.id) AS bid_count,
                       SUM(CASE WHEN b.status='WON' THEN 1 ELSE 0 END) AS won_count,
                       COALESCE(SUM(r.bid_total), 0) AS total_value
                FROM customers c
                JOIN bid_customers bc ON bc.customer_id = c.id
                JOIN bids b ON b.id = bc.bid_id
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE 1=1
            """
            params = []
            if date_from:
                sql += " AND b.original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND b.original_bid_date <= ?"
                params.append(date_to)
            if estimator:
                sql += " AND b.estimator = ?"
                params.append(estimator)
            if status:
                sql += " AND b.status = ?"
                params.append(status)
            sql += " GROUP BY c.id ORDER BY bid_count DESC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_bids_by_location(self, date_from="", date_to="", estimator="", status=""):
        """Group normal bids by free-text location (city)."""
        with self._conn() as conn:
            sql = """
                SELECT CASE
                         WHEN b.location IS NULL OR TRIM(b.location) = '' THEN '(No location)'
                         ELSE TRIM(b.location)
                       END AS location_name,
                       LOWER(CASE
                         WHEN b.location IS NULL OR TRIM(b.location) = '' THEN '(no location)'
                         ELSE TRIM(b.location)
                       END) AS location_key,
                       COUNT(DISTINCT b.id) AS bid_count,
                       SUM(CASE WHEN b.status='WON' THEN 1 ELSE 0 END) AS won_count,
                       COALESCE(SUM(r.bid_total), 0) AS total_value
                FROM bids b
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE COALESCE(b.bid_role, 'normal') != 'parent'
            """
            params = []
            if date_from:
                sql += " AND b.original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND b.original_bid_date <= ?"
                params.append(date_to)
            if estimator:
                sql += " AND b.estimator = ?"
                params.append(estimator)
            if status:
                sql += " AND b.status = ?"
                params.append(status)
            sql += " GROUP BY location_key ORDER BY bid_count DESC, location_name COLLATE NOCASE"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_win_rate(self, date_from="", date_to=""):
        with self._conn() as conn:
            where = "WHERE 1=1"
            params = []
            if date_from:
                where += " AND original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                where += " AND original_bid_date <= ?"
                params.append(date_to)

            overall = conn.execute(
                f"SELECT COUNT(*) as total, SUM(CASE WHEN status='WON' THEN 1 ELSE 0 END) as won FROM bids {where}",
                params,
            ).fetchone()

            by_estimator = conn.execute(
                f"""SELECT estimator, COUNT(*) as total,
                    SUM(CASE WHEN status='WON' THEN 1 ELSE 0 END) as won
                    FROM bids {where} GROUP BY estimator""",
                params,
            ).fetchall()

            overall_rate = 0
            if overall["total"] > 0:
                overall_rate = round(overall["won"] / overall["total"] * 100, 1)

            estimator_rates = []
            for r in by_estimator:
                rate = round(r["won"] / r["total"] * 100, 1) if r["total"] > 0 else 0
                estimator_rates.append({
                    "estimator": r["estimator"],
                    "total": r["total"],
                    "won": r["won"],
                    "rate": rate,
                })

            return {"overall_rate": overall_rate, "by_estimator": estimator_rates}

    def get_monthly_volume(self, date_from="", date_to="", estimator=""):
        with self._conn() as conn:
            sql = """
                SELECT strftime('%Y-%m', b.original_bid_date) AS month,
                       COUNT(*) AS bid_count,
                       COALESCE(SUM(r.bid_total), 0) AS total_value
                FROM bids b
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE 1=1
            """
            params = []
            if date_from:
                sql += " AND b.original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND b.original_bid_date <= ?"
                params.append(date_to)
            if estimator:
                sql += " AND b.estimator = ?"
                params.append(estimator)
            sql += " GROUP BY month ORDER BY month"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def bid_exists(self, bid_name: str, original_bid_date: str, estimator: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                """SELECT COUNT(*) as cnt FROM bids
                   WHERE LOWER(bid_name)=LOWER(?) AND original_bid_date=? AND LOWER(estimator)=LOWER(?)""",
                (bid_name.strip(), original_bid_date, estimator.strip()),
            ).fetchone()
            return row["cnt"] > 0

    def get_all_bids_for_export(self):
        """Return all bids with latest revision data for Excel export."""
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute("""
                    SELECT b.id, b.bid_name, b.estimator, b.original_bid_date, b.status,
                           b.notes, r.bid_total, r.solid_surf_sf, r.stone_sf, r.revision_no,
                           GROUP_CONCAT(c.name, ', ') AS customer_names,
                           wc.name AS won_customer_name
                    FROM bids b
                    LEFT JOIN (
                        SELECT br.*
                        FROM bid_revisions br
                        INNER JOIN (
                            SELECT bid_id, MAX(revision_no) AS max_rev
                            FROM bid_revisions GROUP BY bid_id
                        ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                    ) r ON r.bid_id = b.id
                    LEFT JOIN bid_customers bc ON bc.bid_id = b.id
                    LEFT JOIN customers c ON c.id = bc.customer_id
                    LEFT JOIN customers wc ON wc.id = b.won_customer_id
                    GROUP BY b.id
                    ORDER BY b.original_bid_date ASC
                """).fetchall()
            ]

    # ------------------------------------------------------------------
    # Awarded / Won Bids
    # ------------------------------------------------------------------
    def _reconcile_won_date_with_moraware_created(self, conn, bid_id: int):
        """
        Keep won_date aligned with Moraware created date rules:
        - If won_date is blank and moraware_created_date exists, backfill won_date.
        - If won_date is after moraware_created_date, clamp won_date down.
        """
        conn.execute(
            """
            UPDATE bids
            SET won_date = CASE
                WHEN NULLIF(TRIM(COALESCE(won_date, '')), '') IS NULL
                     AND NULLIF(TRIM(COALESCE(moraware_created_date, '')), '') IS NOT NULL
                THEN moraware_created_date
                WHEN NULLIF(TRIM(COALESCE(won_date, '')), '') IS NOT NULL
                     AND NULLIF(TRIM(COALESCE(moraware_created_date, '')), '') IS NOT NULL
                     AND won_date > moraware_created_date
                THEN moraware_created_date
                ELSE won_date
            END
            WHERE id=?
            """,
            (bid_id,),
        )

    def mark_bid_won(self, bid_id: int, won_customer_id: int,
                     salesperson: str = "", project_manager: str = "",
                     moraware_job_date: str = None, won_notes: str = "",
                     est_complete_date: str = None, est_complete_date_manual: int = None,
                     won_date: str = None):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET status='WON', won_customer_id=?,
                   salesperson=?, project_manager=?,
                   moraware_job_date=CASE WHEN ? IS NULL THEN moraware_job_date ELSE ? END,
                   won_notes=?,
                   est_complete_date=COALESCE(?, est_complete_date),
                   est_complete_date_manual=COALESCE(?, est_complete_date_manual),
                   won_date=CASE WHEN ? IS NULL THEN won_date ELSE ? END
                   WHERE id=?""",
                (won_customer_id, salesperson, project_manager,
                 moraware_job_date, moraware_job_date, won_notes, est_complete_date,
                 est_complete_date_manual, won_date, won_date, bid_id),
            )
            self._reconcile_won_date_with_moraware_created(conn, bid_id)

    def update_won_details(self, bid_id: int, won_customer_id: int,
                           salesperson: str = "", project_manager: str = "",
                           moraware_job_date: str = None, won_notes: str = "",
                           est_complete_date: str = None, est_complete_date_manual: int = None,
                           est_start_month: str = None, won_date: str = None):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET won_customer_id=?,
                   salesperson=?, project_manager=?,
                   moraware_job_date=CASE WHEN ? IS NULL THEN moraware_job_date ELSE ? END,
                   won_notes=?,
                   est_complete_date=COALESCE(?, est_complete_date),
                   est_complete_date_manual=COALESCE(?, est_complete_date_manual),
                   est_start_month=CASE WHEN ? IS NULL THEN est_start_month ELSE ? END,
                   won_date=CASE WHEN ? IS NULL THEN won_date ELSE ? END
                   WHERE id=?""",
                (won_customer_id, salesperson, project_manager,
                 moraware_job_date, moraware_job_date, won_notes, est_complete_date,
                 est_complete_date_manual, est_start_month, est_start_month,
                 won_date, won_date, bid_id),
            )
            self._reconcile_won_date_with_moraware_created(conn, bid_id)

    def get_awarded_bids(
        self,
        search="",
        salesperson="",
        project_manager="",
        year="",
        moraware_status="",
        moraware_sync_state="",
    ):
        with self._conn() as conn:
            sql = """
                SELECT b.*,
                       r.bid_total, r.revision_no,
                       wc.name AS won_customer_name,
                       COALESCE(inv.invoice_status_calc, 'Pending') AS invoice_status_calc
                FROM bids b
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total, br.revision_no
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                LEFT JOIN customers wc ON wc.id = b.won_customer_id
                LEFT JOIN (
                    SELECT bid_id,
                        CASE
                            WHEN COUNT(*) = 0 THEN 'Pending'
                            WHEN SUM(
                                CASE
                                    WHEN LOWER(TRIM(COALESCE(invoice_status, ''))) = 'complete' THEN 1
                                    ELSE 0
                                END
                            ) = COUNT(*) THEN 'Invoiced'
                            WHEN SUM(
                                CASE
                                    WHEN LOWER(TRIM(COALESCE(invoice_status, ''))) = 'complete' THEN 1
                                    ELSE 0
                                END
                            ) > 0 THEN 'Partial'
                            ELSE 'Pending'
                        END AS invoice_status_calc
                    FROM invoice_data GROUP BY bid_id
                ) inv ON inv.bid_id = b.id
                WHERE b.status = 'WON'
                  AND COALESCE(b.bid_role, 'normal') != 'parent'
            """
            params = []
            if search:
                sql += " AND (b.bid_name LIKE ? OR wc.name LIKE ?)"
                params += [f"%{search}%", f"%{search}%"]
            if salesperson:
                sql += " AND b.salesperson = ?"
                params.append(salesperson)
            if project_manager:
                sql += " AND b.project_manager = ?"
                params.append(project_manager)
            if year:
                sql += " AND strftime('%Y', COALESCE(b.won_date, b.original_bid_date)) = ?"
                params.append(str(year))
            if moraware_sync_state == "Synced":
                sql += " AND b.moraware_job_id IS NOT NULL AND b.moraware_job_id != ''"
            elif moraware_sync_state == "Not Synced":
                sql += " AND (b.moraware_job_id IS NULL OR b.moraware_job_id = '')"
            if moraware_status == "Active":
                sql += (
                    " AND b.moraware_job_id IS NOT NULL AND b.moraware_job_id != ''"
                    " AND b.moraware_job_status = 'Active'"
                )
            elif moraware_status == "Complete":
                sql += (
                    " AND b.moraware_job_id IS NOT NULL AND b.moraware_job_id != ''"
                    " AND b.moraware_job_status = 'Complete'"
                )

            sql += " ORDER BY COALESCE(b.won_date, b.original_bid_date) ASC, b.id ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_pending_award_bids(self, search="", project_manager=""):
        """Return WON bids that are not linked to a Moraware job yet."""
        with self._conn() as conn:
            sql = """
                SELECT b.*,
                       r.bid_total, r.revision_no,
                       wc.name AS won_customer_name
                FROM bids b
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total, br.revision_no
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                LEFT JOIN customers wc ON wc.id = b.won_customer_id
                WHERE b.status = 'WON'
                  AND NULLIF(TRIM(COALESCE(b.moraware_job_id, '')), '') IS NULL
                  AND COALESCE(b.bid_role, 'normal') != 'parent'
            """
            params = []
            if search:
                sql += " AND (b.bid_name LIKE ? OR wc.name LIKE ?)"
                params += [f"%{search}%", f"%{search}%"]
            if project_manager:
                sql += " AND b.project_manager = ?"
                params.append(project_manager)
            sql += " ORDER BY COALESCE(b.won_date, b.original_bid_date) ASC, b.id ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def _set_primary_link_in_conn(self, conn, bid_id: int, job_id: str):
        conn.execute("UPDATE bid_moraware_links SET is_primary=0 WHERE bid_id=?", (bid_id,))
        conn.execute(
            "UPDATE bid_moraware_links SET is_primary=1, updated_at=datetime('now') WHERE bid_id=? AND moraware_job_id=?",
            (bid_id, job_id),
        )
        row = conn.execute(
            """
            SELECT moraware_job_id, moraware_job_number
            FROM bid_moraware_links
            WHERE bid_id=? AND is_primary=1
            LIMIT 1
            """,
            (bid_id,),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE bids
                SET moraware_job_id=?, moraware_job_number=COALESCE(NULLIF(TRIM(?), ''), moraware_job_number)
                WHERE id=?
                """,
                (row["moraware_job_id"], row["moraware_job_number"], bid_id),
            )
        else:
            conn.execute(
                "UPDATE bids SET moraware_job_id=NULL, moraware_job_number=NULL WHERE id=?",
                (bid_id,),
            )

    def _get_latest_revision_totals_in_conn(self, conn, bid_id: int) -> dict:
        row = conn.execute(
            """
            SELECT COALESCE(br.bid_total, 0) AS bid_total,
                   COALESCE(br.solid_surf_sf, 0) AS solid_surf_sf,
                   COALESCE(br.stone_sf, 0) AS stone_sf
            FROM bid_revisions br
            INNER JOIN (
                SELECT bid_id, MAX(revision_no) AS max_rev
                FROM bid_revisions
                WHERE bid_id = ?
                GROUP BY bid_id
            ) lr ON lr.bid_id = br.bid_id AND lr.max_rev = br.revision_no
            """,
            (bid_id,),
        ).fetchone()
        if not row:
            return {"bid_total": 0.0, "solid_surf_sf": 0.0, "stone_sf": 0.0}
        return {
            "bid_total": float(row["bid_total"] or 0),
            "solid_surf_sf": float(row["solid_surf_sf"] or 0),
            "stone_sf": float(row["stone_sf"] or 0),
        }

    def get_bid_allocation_target_totals(self, bid_id: int):
        with self._conn() as conn:
            return self._get_latest_revision_totals_in_conn(conn, bid_id)

    def get_bid_link_reference_totals(self, bid_id: int):
        """Reference TP/SF by linked Moraware job from synced invoice rows."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT NULLIF(TRIM(COALESCE(i.moraware_job_id, '')), '') AS moraware_job_id,
                       COALESCE(SUM(COALESCE(i.tp_code, 0)), 0) AS reference_tp_total,
                       COALESCE(SUM(COALESCE(i.sq_ft, 0)), 0) AS reference_sq_ft_total
                FROM invoice_data i
                WHERE i.bid_id=?
                  AND NULLIF(TRIM(COALESCE(i.moraware_job_id, '')), '') IS NOT NULL
                GROUP BY NULLIF(TRIM(COALESCE(i.moraware_job_id, '')), '')
                """,
                (bid_id,),
            ).fetchall()
            return {r["moraware_job_id"]: dict(r) for r in rows if r["moraware_job_id"]}

    def get_bid_moraware_links(self, bid_id: int):
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, bid_id, moraware_job_id, moraware_job_number, moraware_job_name, is_primary, created_at, updated_at
                FROM bid_moraware_links
                WHERE bid_id=?
                ORDER BY is_primary DESC, id ASC
                """,
                (bid_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_bid_moraware_allocations(self, bid_id: int):
        with self._conn() as conn:
            links = conn.execute(
                """
                SELECT l.moraware_job_id,
                       COALESCE(NULLIF(TRIM(l.moraware_job_number), ''), '') AS moraware_job_number,
                       COALESCE(NULLIF(TRIM(l.moraware_job_name), ''), '') AS moraware_job_name,
                       l.is_primary,
                       COALESCE(a.allocated_bid_total, 0) AS allocated_bid_total,
                       COALESCE(a.allocated_solid_surf_sf, 0) AS allocated_solid_surf_sf,
                       COALESCE(a.allocated_stone_sf, 0) AS allocated_stone_sf
                FROM bid_moraware_links l
                LEFT JOIN bid_moraware_allocations a
                  ON a.bid_id = l.bid_id AND a.moraware_job_id = l.moraware_job_id
                WHERE l.bid_id=?
                ORDER BY l.is_primary DESC, l.id ASC
                """,
                (bid_id,),
            ).fetchall()
            refs = self.get_bid_link_reference_totals(bid_id)
            out = []
            for r in links:
                payload = dict(r)
                ref = refs.get(payload["moraware_job_id"]) or {}
                payload["reference_tp_total"] = float(ref.get("reference_tp_total") or 0)
                payload["reference_sq_ft_total"] = float(ref.get("reference_sq_ft_total") or 0)
                out.append(payload)
            return out

    def validate_bid_allocation_totals(self, bid_id: int, rows: list):
        expected = self.get_bid_allocation_target_totals(bid_id)
        actual = {
            "bid_total": sum(float((r or {}).get("allocated_bid_total") or 0) for r in (rows or [])),
            "solid_surf_sf": sum(float((r or {}).get("allocated_solid_surf_sf") or 0) for r in (rows or [])),
            "stone_sf": sum(float((r or {}).get("allocated_stone_sf") or 0) for r in (rows or [])),
        }
        deltas = {
            "bid_total": round(actual["bid_total"] - expected["bid_total"], 2),
            "solid_surf_sf": round(actual["solid_surf_sf"] - expected["solid_surf_sf"], 2),
            "stone_sf": round(actual["stone_sf"] - expected["stone_sf"], 2),
        }
        is_valid = (
            abs(deltas["bid_total"]) <= 0.01
            and abs(deltas["solid_surf_sf"]) <= 0.01
            and abs(deltas["stone_sf"]) <= 0.01
        )
        return {"is_valid": is_valid, "expected": expected, "actual": actual, "delta": deltas}

    def save_bid_moraware_allocations(self, bid_id: int, rows: list):
        norm_rows = []
        seen = set()
        for row in rows or []:
            jid = str((row or {}).get("moraware_job_id") or "").strip()
            if not jid or jid in seen:
                continue
            seen.add(jid)
            norm_rows.append(
                {
                    "moraware_job_id": jid,
                    "allocated_bid_total": float((row or {}).get("allocated_bid_total") or 0),
                    "allocated_solid_surf_sf": float((row or {}).get("allocated_solid_surf_sf") or 0),
                    "allocated_stone_sf": float((row or {}).get("allocated_stone_sf") or 0),
                }
            )

        check = self.validate_bid_allocation_totals(bid_id, norm_rows)
        if not check["is_valid"]:
            raise ValueError(
                "Allocation totals must exactly match latest revision totals. "
                f"Expected={check['expected']} Actual={check['actual']} Delta={check['delta']}"
            )

        with self._conn() as conn:
            link_rows = conn.execute(
                "SELECT moraware_job_id FROM bid_moraware_links WHERE bid_id=?",
                (bid_id,),
            ).fetchall()
            valid_ids = {str(r["moraware_job_id"]).strip() for r in link_rows}
            for r in norm_rows:
                if r["moraware_job_id"] not in valid_ids:
                    raise ValueError(f"Cannot allocate to unlinked Moraware job: {r['moraware_job_id']}")
            conn.execute("DELETE FROM bid_moraware_allocations WHERE bid_id=?", (bid_id,))
            for r in norm_rows:
                conn.execute(
                    """
                    INSERT INTO bid_moraware_allocations
                        (bid_id, moraware_job_id, allocated_bid_total, allocated_solid_surf_sf, allocated_stone_sf, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        bid_id,
                        r["moraware_job_id"],
                        r["allocated_bid_total"],
                        r["allocated_solid_surf_sf"],
                        r["allocated_stone_sf"],
                    ),
                )

    def split_bid_from_moraware_jobs(self, bid_id: int):
        """
        Split one WON bid into child WON bids, one per linked Moraware job.
        Parent bid is retained as historical container and excluded from rollups.
        """
        with self._conn() as conn:
            parent = conn.execute("SELECT * FROM bids WHERE id=?", (bid_id,)).fetchone()
            if not parent:
                raise ValueError("Bid not found.")
            if (parent["status"] or "").strip().upper() != "WON":
                raise ValueError("Only WON bids can be split.")
            if str(parent["bid_role"] or "normal").strip().lower() == "child":
                raise ValueError("Cannot split a child bid.")

            existing_children = conn.execute(
                "SELECT COUNT(*) AS cnt FROM bids WHERE parent_bid_id=? AND COALESCE(bid_role, 'normal')='child'",
                (bid_id,),
            ).fetchone()
            if int((existing_children["cnt"] if existing_children else 0) or 0) > 0:
                raise ValueError("This bid has already been split.")

            links = conn.execute(
                """
                SELECT l.moraware_job_id,
                       COALESCE(NULLIF(TRIM(l.moraware_job_number), ''), '') AS moraware_job_number,
                       COALESCE(NULLIF(TRIM(l.moraware_job_name), ''), '') AS moraware_job_name,
                       l.is_primary,
                       COALESCE(a.allocated_bid_total, 0) AS allocated_bid_total,
                       COALESCE(a.allocated_solid_surf_sf, 0) AS allocated_solid_surf_sf,
                       COALESCE(a.allocated_stone_sf, 0) AS allocated_stone_sf
                FROM bid_moraware_links l
                LEFT JOIN bid_moraware_allocations a
                  ON a.bid_id=l.bid_id AND a.moraware_job_id=l.moraware_job_id
                WHERE l.bid_id=?
                ORDER BY l.is_primary DESC, l.id ASC
                """,
                (bid_id,),
            ).fetchall()
            if len(links) < 2:
                raise ValueError("At least two linked Moraware jobs are required to split this bid.")

            check = self.validate_bid_allocation_totals(
                bid_id,
                [
                    {
                        "moraware_job_id": r["moraware_job_id"],
                        "allocated_bid_total": float(r["allocated_bid_total"] or 0),
                        "allocated_solid_surf_sf": float(r["allocated_solid_surf_sf"] or 0),
                        "allocated_stone_sf": float(r["allocated_stone_sf"] or 0),
                    }
                    for r in links
                ],
            )
            if not check["is_valid"]:
                raise ValueError(
                    "Split allocation totals must match bid totals before splitting. "
                    f"Delta={check['delta']}"
                )

            customer_rows = conn.execute(
                "SELECT customer_id FROM bid_customers WHERE bid_id=?",
                (bid_id,),
            ).fetchall()
            customer_ids = [int(r["customer_id"]) for r in customer_rows]
            child_ids = []

            for idx, r in enumerate(links, start=1):
                job_id = str(r["moraware_job_id"] or "").strip()
                if not job_id:
                    continue
                job_number = str(r["moraware_job_number"] or "").strip()
                job_name = str(r.get("moraware_job_name") or "").strip()
                child_name = job_name or (f"{parent['bid_name']} - {job_number}" if job_number else f"{parent['bid_name']} - Job {job_id}")

                cur = conn.execute(
                    """
                    INSERT INTO bids (
                        bid_name, estimator, original_bid_date, status, won_customer_id, notes,
                        salesperson, project_manager, moraware_job_date, won_date, won_notes,
                        moraware_job_id, moraware_job_number, moraware_job_status, last_moraware_sync_at,
                        est_complete_date, est_complete_date_manual, est_start_month, moraware_created_date,
                        notebook_notes, parent_bid_id, bid_role, exclude_from_rollups
                    ) VALUES (?, ?, ?, 'WON', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'child', 0)
                    """,
                    (
                        child_name,
                        parent["estimator"],
                        parent["original_bid_date"],
                        parent["won_customer_id"],
                        parent["notes"],
                        parent["salesperson"],
                        parent["project_manager"],
                        parent["moraware_job_date"],
                        parent["won_date"],
                        parent["won_notes"],
                        job_id,
                        job_number or None,
                        parent["moraware_job_status"],
                        parent["last_moraware_sync_at"],
                        parent["est_complete_date"],
                        parent["est_complete_date_manual"],
                        parent["est_start_month"],
                        parent["moraware_created_date"],
                        parent["notebook_notes"],
                        bid_id,
                    ),
                )
                child_id = int(cur.lastrowid)
                child_ids.append(child_id)

                for cid in customer_ids:
                    conn.execute(
                        "INSERT INTO bid_customers (bid_id, customer_id) VALUES (?, ?)",
                        (child_id, cid),
                    )

                conn.execute(
                    """
                    INSERT INTO bid_revisions
                        (bid_id, revision_no, revision_date, bid_total, solid_surf_sf, stone_sf, reason)
                    VALUES (?, 1, ?, ?, ?, ?, ?)
                    """,
                    (
                        child_id,
                        parent["original_bid_date"],
                        float(r["allocated_bid_total"] or 0),
                        float(r["allocated_solid_surf_sf"] or 0),
                        float(r["allocated_stone_sf"] or 0),
                        f"Split from parent bid #{bid_id} ({idx}/{len(links)})",
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO bid_moraware_links (bid_id, moraware_job_id, moraware_job_number, is_primary)
                    VALUES (?, ?, ?, 1)
                    """,
                    (child_id, job_id, job_number or None),
                )
                conn.execute(
                    """
                    INSERT INTO bid_moraware_allocations
                        (bid_id, moraware_job_id, allocated_bid_total, allocated_solid_surf_sf, allocated_stone_sf, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        child_id,
                        job_id,
                        float(r["allocated_bid_total"] or 0),
                        float(r["allocated_solid_surf_sf"] or 0),
                        float(r["allocated_stone_sf"] or 0),
                    ),
                )

                invoice_rows = conn.execute(
                    """
                    SELECT phase, tp_code, sq_ft, invoice_date, template_date, install_date,
                           contact_customer_date, contact_customer_notes, invoice_status, source
                    FROM invoice_data
                    WHERE bid_id=? AND NULLIF(TRIM(COALESCE(moraware_job_id, '')), '')=?
                    """,
                    (bid_id, job_id),
                ).fetchall()
                for inv in invoice_rows:
                    conn.execute(
                        """
                        INSERT INTO invoice_data
                            (bid_id, moraware_job_id, phase, tp_code, sq_ft, invoice_date, template_date,
                             install_date, contact_customer_date, contact_customer_notes, invoice_status, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            child_id,
                            job_id,
                            inv["phase"],
                            inv["tp_code"],
                            inv["sq_ft"],
                            inv["invoice_date"],
                            inv["template_date"],
                            inv["install_date"],
                            inv["contact_customer_date"],
                            inv["contact_customer_notes"],
                            inv["invoice_status"],
                            inv["source"],
                        ),
                    )

            conn.execute(
                """
                UPDATE bids
                SET bid_role='parent',
                    exclude_from_rollups=1
                WHERE id=?
                """,
                (bid_id,),
            )
            return child_ids

    def add_bid_moraware_link(
        self,
        bid_id: int,
        job_id: str,
        job_number: str = "",
        make_primary: bool = False,
        job_name: str = "",
    ):
        job_id = str(job_id or "").strip()
        if not job_id:
            return
        job_number = (job_number or "").strip()
        job_name = (job_name or "").strip()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO bid_moraware_links (bid_id, moraware_job_id, moraware_job_number, moraware_job_name, is_primary)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(bid_id, moraware_job_id) DO UPDATE SET
                    moraware_job_number=CASE
                        WHEN excluded.moraware_job_number IS NULL OR TRIM(excluded.moraware_job_number) = ''
                        THEN bid_moraware_links.moraware_job_number
                        ELSE excluded.moraware_job_number
                    END,
                    moraware_job_name=CASE
                        WHEN excluded.moraware_job_name IS NULL OR TRIM(excluded.moraware_job_name) = ''
                        THEN bid_moraware_links.moraware_job_name
                        ELSE excluded.moraware_job_name
                    END,
                    updated_at=datetime('now')
                """,
                (bid_id, job_id, job_number or None, job_name or None),
            )
            has_primary = conn.execute(
                "SELECT 1 FROM bid_moraware_links WHERE bid_id=? AND is_primary=1 LIMIT 1",
                (bid_id,),
            ).fetchone()
            if make_primary or not has_primary:
                self._set_primary_link_in_conn(conn, bid_id, job_id)
            alloc_exists = conn.execute(
                "SELECT 1 FROM bid_moraware_allocations WHERE bid_id=? AND moraware_job_id=? LIMIT 1",
                (bid_id, job_id),
            ).fetchone()
            if not alloc_exists:
                totals = self._get_latest_revision_totals_in_conn(conn, bid_id)
                total_links = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM bid_moraware_links WHERE bid_id=?",
                    (bid_id,),
                ).fetchone()
                if int((total_links["cnt"] if total_links else 0) or 0) <= 1:
                    alloc_bid_total = totals["bid_total"]
                    alloc_ss = totals["solid_surf_sf"]
                    alloc_st = totals["stone_sf"]
                else:
                    alloc_bid_total = 0.0
                    alloc_ss = 0.0
                    alloc_st = 0.0
                conn.execute(
                    """
                    INSERT INTO bid_moraware_allocations
                        (bid_id, moraware_job_id, allocated_bid_total, allocated_solid_surf_sf, allocated_stone_sf, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(bid_id, moraware_job_id) DO NOTHING
                    """,
                    (bid_id, job_id, alloc_bid_total, alloc_ss, alloc_st),
                )

    def remove_bid_moraware_link(self, bid_id: int, job_id: str):
        job_id = str(job_id or "").strip()
        if not job_id:
            return
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM bid_moraware_links WHERE bid_id=? AND moraware_job_id=?",
                (bid_id, job_id),
            )
            conn.execute(
                "DELETE FROM bid_moraware_allocations WHERE bid_id=? AND moraware_job_id=?",
                (bid_id, job_id),
            )
            primary = conn.execute(
                "SELECT moraware_job_id FROM bid_moraware_links WHERE bid_id=? AND is_primary=1 LIMIT 1",
                (bid_id,),
            ).fetchone()
            if not primary:
                fallback = conn.execute(
                    "SELECT moraware_job_id FROM bid_moraware_links WHERE bid_id=? ORDER BY id ASC LIMIT 1",
                    (bid_id,),
                ).fetchone()
                if fallback:
                    self._set_primary_link_in_conn(conn, bid_id, fallback["moraware_job_id"])
                else:
                    conn.execute(
                        "UPDATE bids SET moraware_job_id=NULL, moraware_job_number=NULL, moraware_job_status=NULL, last_moraware_sync_at=NULL WHERE id=?",
                        (bid_id,),
                    )
                    conn.execute("DELETE FROM invoice_data WHERE bid_id=?", (bid_id,))
                    conn.execute("DELETE FROM bid_moraware_allocations WHERE bid_id=?", (bid_id,))

    def set_primary_bid_moraware_link(self, bid_id: int, job_id: str):
        job_id = str(job_id or "").strip()
        if not job_id:
            return
        with self._conn() as conn:
            exists = conn.execute(
                "SELECT 1 FROM bid_moraware_links WHERE bid_id=? AND moraware_job_id=? LIMIT 1",
                (bid_id, job_id),
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO bid_moraware_links (bid_id, moraware_job_id, is_primary) VALUES (?, ?, 0)",
                    (bid_id, job_id),
                )
            alloc_exists = conn.execute(
                "SELECT 1 FROM bid_moraware_allocations WHERE bid_id=? AND moraware_job_id=? LIMIT 1",
                (bid_id, job_id),
            ).fetchone()
            if not alloc_exists:
                conn.execute(
                    """
                    INSERT INTO bid_moraware_allocations
                        (bid_id, moraware_job_id, allocated_bid_total, allocated_solid_surf_sf, allocated_stone_sf, updated_at)
                    VALUES (?, ?, 0, 0, 0, datetime('now'))
                    """,
                    (bid_id, job_id),
                )
            self._set_primary_link_in_conn(conn, bid_id, job_id)

    def get_bids_for_moraware_job_id(self, job_id: str):
        return self.get_bids_linked_to_moraware_job_id(job_id)

    def get_primary_bid_link_map_by_job_ids(self, moraware_job_ids: list[str]):
        cleaned_ids = []
        seen = set()
        for raw in moraware_job_ids or []:
            jid = str(raw or "").strip()
            if not jid or jid in seen:
                continue
            cleaned_ids.append(jid)
            seen.add(jid)
        if not cleaned_ids:
            return {}

        placeholders = ",".join(["?"] * len(cleaned_ids))
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT b.id,
                       b.bid_name,
                       b.status,
                       l.moraware_job_id,
                       COALESCE(NULLIF(TRIM(l.moraware_job_number), ''), b.moraware_job_number, '') AS moraware_job_number,
                       b.project_manager,
                       b.salesperson,
                       b.original_bid_date,
                       b.moraware_job_date,
                       wc.name AS won_customer_name,
                       r.bid_total
                FROM bid_moraware_links l
                JOIN bids b ON b.id = l.bid_id
                LEFT JOIN customers wc ON wc.id = b.won_customer_id
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE l.is_primary = 1
                  AND NULLIF(TRIM(COALESCE(l.moraware_job_id, '')), '') IN ({placeholders})
                ORDER BY COALESCE(b.won_date, b.original_bid_date) DESC, b.id DESC
                """,
                cleaned_ids,
            ).fetchall()

        mapping = {}
        for row in rows:
            payload = dict(row)
            jid = (payload.get("moraware_job_id") or "").strip()
            if jid and jid not in mapping:
                mapping[jid] = payload
        return mapping

    def get_bid_links_by_moraware_job_ids(self, moraware_job_ids: list[str]):
        """
        Return a mapping of Moraware Job ID -> linked local bid metadata.

        If duplicates exist, the most recently won/created bid row wins by ORDER BY.
        """
        return self.get_primary_bid_link_map_by_job_ids(moraware_job_ids)

    def get_all_bid_links_by_moraware_job_ids(self, moraware_job_ids: list[str]):
        """
        Return a mapping of Moraware Job ID -> list of linked local bid metadata.
        Includes both primary and secondary links.
        """
        cleaned_ids = []
        seen = set()
        for raw in moraware_job_ids or []:
            jid = str(raw or "").strip()
            if not jid or jid in seen:
                continue
            cleaned_ids.append(jid)
            seen.add(jid)
        if not cleaned_ids:
            return {}

        placeholders = ",".join(["?"] * len(cleaned_ids))
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT b.id,
                       b.bid_name,
                       b.status,
                       l.moraware_job_id,
                       COALESCE(NULLIF(TRIM(l.moraware_job_number), ''), b.moraware_job_number, '') AS moraware_job_number,
                       b.project_manager,
                       b.salesperson,
                       b.original_bid_date,
                       b.moraware_job_date,
                       wc.name AS won_customer_name,
                       r.bid_total,
                       l.is_primary
                FROM bid_moraware_links l
                JOIN bids b ON b.id = l.bid_id
                LEFT JOIN customers wc ON wc.id = b.won_customer_id
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE NULLIF(TRIM(COALESCE(l.moraware_job_id, '')), '') IN ({placeholders})
                ORDER BY COALESCE(b.won_date, b.original_bid_date) DESC, b.id DESC
                """,
                cleaned_ids,
            ).fetchall()

        mapping = {jid: [] for jid in cleaned_ids}
        for row in rows:
            payload = dict(row)
            jid = (payload.get("moraware_job_id") or "").strip()
            if not jid:
                continue
            mapping.setdefault(jid, []).append(payload)
        return mapping

    def get_bids_linked_to_moraware_job_id(self, moraware_job_id: str):
        """Return all local bids currently linked to one Moraware job id."""
        jid = str(moraware_job_id or "").strip()
        if not jid:
            return []
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT b.id,
                       b.bid_name,
                       b.status,
                       l.moraware_job_id,
                       COALESCE(NULLIF(TRIM(l.moraware_job_number), ''), b.moraware_job_number, '') AS moraware_job_number,
                       b.project_manager,
                       b.salesperson,
                       b.original_bid_date,
                       b.moraware_job_date,
                       l.is_primary,
                       wc.name AS won_customer_name
                FROM bid_moraware_links l
                JOIN bids b ON b.id = l.bid_id
                LEFT JOIN customers wc ON wc.id = b.won_customer_id
                WHERE NULLIF(TRIM(COALESCE(l.moraware_job_id, '')), '') = ?
                ORDER BY l.is_primary DESC, COALESCE(b.won_date, b.original_bid_date) DESC, b.id DESC
                """,
                (jid,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_linkable_bids(self, search: str = ""):
        """Return all bids eligible for manual link selection."""
        return self.get_bids(search=search or "")

    def get_awarded_stats(self):
        with self._conn() as conn:
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM bids WHERE status='WON' AND COALESCE(exclude_from_rollups, 0)=0"
            ).fetchone()
            total_awarded = count_row["cnt"] if count_row else 0

            value_row = conn.execute("""
                WITH latest_rev AS (
                    SELECT br.bid_id, COALESCE(br.bid_total, 0) AS bid_total
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ),
                alloc AS (
                    SELECT a.bid_id, COALESCE(SUM(a.allocated_bid_total), 0) AS allocated_total
                    FROM bid_moraware_allocations a
                    GROUP BY a.bid_id
                )
                SELECT COALESCE(SUM(
                    CASE
                        WHEN alloc.bid_id IS NOT NULL THEN alloc.allocated_total
                        ELSE COALESCE(lr.bid_total, 0)
                    END
                ), 0) AS total_value
                FROM bids b
                LEFT JOIN latest_rev lr ON lr.bid_id = b.id
                LEFT JOIN alloc ON alloc.bid_id = b.id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
            """).fetchone()
            total_won_value = value_row["total_value"] if value_row else 0

            inv_row = conn.execute("""
                SELECT COALESCE(SUM(id2.tp_code), 0) AS total_invoiced
                FROM invoice_data id2
                JOIN bids b ON b.id = id2.bid_id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND LOWER(TRIM(COALESCE(id2.invoice_status, ''))) = 'complete'
            """).fetchone()
            total_invoiced = inv_row["total_invoiced"] if inv_row else 0

            avg_job_size = total_won_value / total_awarded if total_awarded > 0 else 0

            return {
                "total_awarded": total_awarded,
                "total_won_value": total_won_value,
                "total_invoiced": total_invoiced,
                "avg_job_size": avg_job_size,
            }

    def get_invoice_data_for_bid(self, bid_id: int):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM invoice_data WHERE bid_id=? ORDER BY phase, COALESCE(moraware_job_id, '')",
                    (bid_id,),
                ).fetchall()
            ]

    def upsert_invoice_data(self, bid_id: int, phases: list):
        """Replace all invoice_data for a bid with fresh phase rows."""
        with self._conn() as conn:
            conn.execute("DELETE FROM invoice_data WHERE bid_id=?", (bid_id,))
            for p in phases:
                conn.execute(
                    """INSERT INTO invoice_data
                       (bid_id, moraware_job_id, phase, tp_code, sq_ft, invoice_date, template_date,
                        install_date, contact_customer_date, contact_customer_notes,
                        invoice_status, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        bid_id,
                        (p.get("moraware_job_id") or "").strip() or None,
                        p.get("phase"),
                        p.get("tp_code"),
                        p.get("sq_ft"),
                        p.get("invoice_date"),
                        p.get("template_date"),
                        p.get("install_date"),
                        p.get("contact_customer_date"),
                        p.get("contact_customer_notes"),
                        p.get("invoice_status"),
                        p.get("source"),
                    ),
                )

            manual_row = conn.execute(
                "SELECT COALESCE(est_complete_date_manual, 0) AS manual FROM bids WHERE id=?",
                (bid_id,),
            ).fetchone()
            manual_override = bool(manual_row and manual_row["manual"] == 1)
            if not manual_override:
                est_row = conn.execute(
                    """SELECT MAX(install_date) AS est_complete_date
                       FROM invoice_data
                       WHERE bid_id = ? AND NULLIF(TRIM(install_date), '') IS NOT NULL""",
                    (bid_id,),
                ).fetchone()
                conn.execute(
                    "UPDATE bids SET est_complete_date=? WHERE id=?",
                    ((est_row["est_complete_date"] if est_row else None), bid_id),
                )

    def get_pm_notebook_status(self):
        """Return notebook status per WON bid: Active or Pending."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT b.id AS bid_id,
                       CASE
                           WHEN COALESCE(
                               MAX(CASE
                                   WHEN NULLIF(TRIM(i.template_date), '') IS NOT NULL THEN 1
                                   ELSE 0
                               END),
                               0
                           ) = 1 THEN 'Active'
                           ELSE 'Pending'
                       END AS notebook_status
                FROM bids b
                LEFT JOIN invoice_data i ON i.bid_id = b.id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                GROUP BY b.id
                ORDER BY b.id
                """
            ).fetchall()
            return {r["bid_id"]: r["notebook_status"] for r in rows}

    def get_pm_job_type(self):
        """Return derived job type per WON bid."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                WITH phase_flags AS (
                    SELECT bid_id,
                           MAX(CASE WHEN UPPER(TRIM(COALESCE(phase, ''))) LIKE 'SS%' THEN 1 ELSE 0 END) AS has_ss_phase,
                           MAX(CASE WHEN UPPER(TRIM(COALESCE(phase, ''))) LIKE 'ST%' THEN 1 ELSE 0 END) AS has_st_phase
                    FROM invoice_data
                    GROUP BY bid_id
                ),
                latest_rev AS (
                    SELECT br.bid_id, br.solid_surf_sf, br.stone_sf
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions
                        GROUP BY bid_id
                    ) lr ON lr.bid_id = br.bid_id AND lr.max_rev = br.revision_no
                )
                SELECT b.id AS bid_id,
                       CASE
                           WHEN COALESCE(pf.has_ss_phase, 0) = 1 AND COALESCE(pf.has_st_phase, 0) = 1 THEN 'Mixed'
                           WHEN COALESCE(pf.has_ss_phase, 0) = 1 THEN 'Solid Surface'
                           WHEN COALESCE(pf.has_st_phase, 0) = 1 THEN 'Stone'
                           WHEN COALESCE(lr.solid_surf_sf, 0) > 0 AND COALESCE(lr.stone_sf, 0) > 0 THEN 'Mixed'
                           WHEN COALESCE(lr.solid_surf_sf, 0) > 0 THEN 'Solid Surface'
                           WHEN COALESCE(lr.stone_sf, 0) > 0 THEN 'Stone'
                           ELSE 'Unassigned'
                       END AS job_type
                FROM bids b
                LEFT JOIN phase_flags pf ON pf.bid_id = b.id
                LEFT JOIN latest_rev lr ON lr.bid_id = b.id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                ORDER BY b.id
                """
            ).fetchall()
            return {r["bid_id"]: r["job_type"] for r in rows}

    def get_pm_overview_stats(self):
        """
        Return PM overview rollups for the current month:
        - complete totals from completed invoice phases in month
        - projected totals from est_complete_date in month with no complete phases
        - pipeline counts from derived notebook status
        """
        with self._conn() as conn:
            now = datetime.now()
            month_start = now.replace(day=1).strftime("%Y-%m-%d")
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            month_end = next_month.strftime("%Y-%m-%d")

            job_type_map = self.get_pm_job_type()
            status_map = self.get_pm_notebook_status()

            complete_rows = conn.execute(
                """
                SELECT i.bid_id,
                       COALESCE(SUM(i.tp_code), 0) AS dollars,
                       COALESCE(SUM(i.sq_ft), 0) AS sq_ft
                FROM invoice_data i
                JOIN bids b ON b.id = i.bid_id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND LOWER(TRIM(COALESCE(i.invoice_status, ''))) = 'complete'
                  AND NULLIF(TRIM(i.invoice_date), '') IS NOT NULL
                  AND i.invoice_date >= ?
                  AND i.invoice_date < ?
                GROUP BY i.bid_id
                """,
                (month_start, month_end),
            ).fetchall()

            has_complete_rows = conn.execute(
                """
                SELECT bid_id,
                       MAX(CASE WHEN LOWER(TRIM(COALESCE(invoice_status, ''))) = 'complete' THEN 1 ELSE 0 END) AS has_complete
                FROM invoice_data
                GROUP BY bid_id
                """
            ).fetchall()
            has_complete_map = {r["bid_id"]: bool(r["has_complete"]) for r in has_complete_rows}

            projected_rows = conn.execute(
                """
                WITH latest_rev AS (
                    SELECT br.bid_id, br.bid_total, br.solid_surf_sf, br.stone_sf
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions
                        GROUP BY bid_id
                    ) lr ON lr.bid_id = br.bid_id AND lr.max_rev = br.revision_no
                ),
                alloc AS (
                    SELECT a.bid_id,
                           COALESCE(SUM(a.allocated_bid_total), 0) AS alloc_bid_total,
                           COALESCE(SUM(a.allocated_solid_surf_sf), 0) AS alloc_solid_surf_sf,
                           COALESCE(SUM(a.allocated_stone_sf), 0) AS alloc_stone_sf
                    FROM bid_moraware_allocations a
                    GROUP BY a.bid_id
                )
                SELECT b.id AS bid_id,
                       CASE
                           WHEN alloc.bid_id IS NOT NULL THEN COALESCE(alloc.alloc_bid_total, 0)
                           ELSE COALESCE(lr.bid_total, 0)
                       END AS bid_total,
                       CASE
                           WHEN alloc.bid_id IS NOT NULL THEN COALESCE(alloc.alloc_solid_surf_sf, 0) + COALESCE(alloc.alloc_stone_sf, 0)
                           ELSE COALESCE(lr.solid_surf_sf, 0) + COALESCE(lr.stone_sf, 0)
                       END AS total_sq_ft
                FROM bids b
                LEFT JOIN latest_rev lr ON lr.bid_id = b.id
                LEFT JOIN alloc ON alloc.bid_id = b.id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND NULLIF(TRIM(b.est_complete_date), '') IS NOT NULL
                  AND b.est_complete_date >= ?
                  AND b.est_complete_date < ?
                """,
                (month_start, month_end),
            ).fetchall()

            categories = ("Solid Surface", "Stone", "Mixed", "Unassigned")
            zero_bucket = {k: 0.0 for k in categories}
            complete_dollars = dict(zero_bucket)
            complete_sqft = dict(zero_bucket)
            projected_dollars = dict(zero_bucket)
            projected_sqft = dict(zero_bucket)

            for row in complete_rows:
                jt = job_type_map.get(row["bid_id"], "Unassigned")
                if jt not in complete_dollars:
                    jt = "Unassigned"
                complete_dollars[jt] += float(row["dollars"] or 0)
                complete_sqft[jt] += float(row["sq_ft"] or 0)

            for row in projected_rows:
                if has_complete_map.get(row["bid_id"], False):
                    continue
                jt = job_type_map.get(row["bid_id"], "Unassigned")
                if jt not in projected_dollars:
                    jt = "Unassigned"
                projected_dollars[jt] += float(row["bid_total"] or 0)
                projected_sqft[jt] += float(row["total_sq_ft"] or 0)

            active_jobs = sum(1 for st in status_map.values() if st == "Active")
            pending_jobs = sum(1 for st in status_map.values() if st == "Pending")

            total_dollars = {
                k: complete_dollars[k] + projected_dollars[k]
                for k in categories
            }
            total_sqft = {
                k: complete_sqft[k] + projected_sqft[k]
                for k in categories
            }

            return {
                "month": now.strftime("%Y-%m"),
                "current_month": {
                    "complete": {
                        "dollars": complete_dollars,
                        "sq_ft": complete_sqft,
                        "total_dollars": sum(complete_dollars.values()),
                        "total_sq_ft": sum(complete_sqft.values()),
                    },
                    "projected": {
                        "dollars": projected_dollars,
                        "sq_ft": projected_sqft,
                        "total_dollars": sum(projected_dollars.values()),
                        "total_sq_ft": sum(projected_sqft.values()),
                    },
                    "total": {
                        "dollars": total_dollars,
                        "sq_ft": total_sqft,
                        "total_dollars": sum(total_dollars.values()),
                        "total_sq_ft": sum(total_sqft.values()),
                    },
                },
                "pipeline": {
                    "active_jobs": active_jobs,
                    "pending_jobs": pending_jobs,
                    "total_jobs": active_jobs + pending_jobs,
                },
            }

    def get_pm_completed_history(self, limit: int = 12):
        """Return completed monthly history from invoice data only."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT strftime('%Y-%m-01', i.invoice_date) AS month,
                       COALESCE(SUM(i.tp_code), 0) AS revenue,
                       COALESCE(SUM(CASE WHEN UPPER(TRIM(COALESCE(i.phase, ''))) LIKE 'SS%' THEN i.sq_ft ELSE 0 END), 0) AS solid_surf_sf,
                       COALESCE(SUM(CASE WHEN UPPER(TRIM(COALESCE(i.phase, ''))) LIKE 'ST%' THEN i.sq_ft ELSE 0 END), 0) AS stone_sf
                FROM invoice_data i
                JOIN bids b ON b.id = i.bid_id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND NULLIF(TRIM(COALESCE(b.moraware_job_id, '')), '') IS NOT NULL
                  AND LOWER(TRIM(COALESCE(i.invoice_status, ''))) = 'complete'
                  AND NULLIF(TRIM(i.invoice_date), '') IS NOT NULL
                GROUP BY strftime('%Y-%m-01', i.invoice_date)
                ORDER BY month DESC
                LIMIT ?
                """,
                (max(1, int(limit or 12)),),
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    def get_pm_pipeline_forecast(self, days_ahead: int = 90):
        """Return pipeline forecast and needs-sync queues from Moraware-synced invoice data only."""
        now = datetime.now()
        window_start = now.strftime("%Y-%m-%d")
        window_end_dt = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=max(1, int(days_ahead or 90))
        )
        window_end = window_end_dt.strftime("%Y-%m-%d")

        start_month = now.replace(day=1)
        end_month = window_end_dt.replace(day=1)
        horizon_months = []
        month_cursor = start_month
        while month_cursor <= end_month:
            horizon_months.append(month_cursor.strftime("%Y-%m-01"))
            if month_cursor.month == 12:
                month_cursor = month_cursor.replace(year=month_cursor.year + 1, month=1, day=1)
            else:
                month_cursor = month_cursor.replace(month=month_cursor.month + 1, day=1)
        horizon_set = set(horizon_months)

        def month_floor(date_text: str):
            val = (date_text or "").strip()
            if not val:
                return ""
            if len(val) >= 10:
                val = val[:10]
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                try:
                    d = datetime.strptime(val, fmt)
                    return d.strftime("%Y-%m-01")
                except ValueError:
                    continue
            if len(val) == 7:
                return f"{val}-01"
            return ""

        def parse_date(date_text: str):
            val = (date_text or "").strip()
            if not val:
                return None
            if len(val) >= 10:
                val = val[:10]
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
            if len(val) == 7:
                try:
                    return datetime.strptime(f"{val}-01", "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        with self._conn() as conn:
            rows = conn.execute(
                """
                WITH phase_rollup AS (
                    SELECT i.bid_id,
                           COALESCE(SUM(i.tp_code), 0) AS total_tp,
                           COALESCE(SUM(i.sq_ft), 0) AS total_sq_ft,
                           COUNT(*) AS phase_count,
                           SUM(CASE WHEN LOWER(TRIM(COALESCE(i.invoice_status, ''))) = 'complete' THEN 1 ELSE 0 END) AS complete_count,
                           MAX(CASE WHEN NULLIF(TRIM(i.template_date), '') IS NOT NULL THEN 1 ELSE 0 END) AS has_template,
                           MIN(CASE WHEN NULLIF(TRIM(i.template_date), '') IS NOT NULL THEN i.template_date END) AS first_template_date
                    FROM invoice_data i
                    GROUP BY i.bid_id
                ),
                alloc AS (
                    SELECT a.bid_id,
                           COALESCE(SUM(a.allocated_bid_total), 0) AS alloc_total_tp,
                           COALESCE(SUM(a.allocated_solid_surf_sf), 0) + COALESCE(SUM(a.allocated_stone_sf), 0) AS alloc_total_sq_ft
                    FROM bid_moraware_allocations a
                    GROUP BY a.bid_id
                )
                SELECT b.id AS bid_id,
                       b.bid_name,
                       b.project_manager,
                       b.est_start_month,
                       CASE
                           WHEN alloc.bid_id IS NOT NULL THEN COALESCE(alloc.alloc_total_tp, 0)
                           ELSE COALESCE(pr.total_tp, 0)
                       END AS total_tp,
                       CASE
                           WHEN alloc.bid_id IS NOT NULL THEN COALESCE(alloc.alloc_total_sq_ft, 0)
                           ELSE COALESCE(pr.total_sq_ft, 0)
                       END AS total_sq_ft,
                       COALESCE(pr.phase_count, 0) AS phase_count,
                       COALESCE(pr.complete_count, 0) AS complete_count,
                       COALESCE(pr.has_template, 0) AS has_template,
                       pr.first_template_date
                FROM bids b
                LEFT JOIN phase_rollup pr ON pr.bid_id = b.id
                LEFT JOIN alloc ON alloc.bid_id = b.id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND NULLIF(TRIM(COALESCE(b.moraware_job_id, '')), '') IS NOT NULL
                  AND NULLIF(TRIM(COALESCE(b.moraware_job_status, '')), '') IS NOT NULL
                ORDER BY b.id
                """
            ).fetchall()

            needs_sync_rows = conn.execute(
                """
                SELECT b.id AS bid_id,
                       b.bid_name,
                       b.project_manager,
                       b.moraware_job_id,
                       b.moraware_job_status
                FROM bids b
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND (
                        NULLIF(TRIM(COALESCE(b.moraware_job_id, '')), '') IS NULL
                        OR NULLIF(TRIM(COALESCE(b.moraware_job_status, '')), '') IS NULL
                  )
                ORDER BY b.bid_name COLLATE NOCASE
                """
            ).fetchall()

            backlog = {
                "In Progress": {"jobs": 0, "dollars": 0.0, "sq_ft": 0.0},
                "Unscheduled": {"jobs": 0, "dollars": 0.0, "sq_ft": 0.0},
                "Complete": {"jobs": 0, "dollars": 0.0, "sq_ft": 0.0},
            }
            unscheduled_jobs = []
            plus_90 = {
                "start_confirmed_dollars": 0.0,
                "start_confirmed_sq_ft": 0.0,
                "start_estimated_dollars": 0.0,
                "start_estimated_sq_ft": 0.0,
            }
            monthly = {
                m: {
                    "start_confirmed_dollars": 0.0,
                    "start_confirmed_sq_ft": 0.0,
                    "start_estimated_dollars": 0.0,
                    "start_estimated_sq_ft": 0.0,
                }
                for m in horizon_months
            }

            for r in rows:
                total_tp = float(r["total_tp"] or 0)
                total_sq_ft = float(r["total_sq_ft"] or 0)
                phase_count = int(r["phase_count"] or 0)
                complete_count = int(r["complete_count"] or 0)
                has_template = int(r["has_template"] or 0) == 1

                is_complete = phase_count > 0 and complete_count == phase_count
                if is_complete:
                    state = "Complete"
                elif has_template:
                    state = "In Progress"
                else:
                    state = "Unscheduled"

                backlog[state]["jobs"] += 1
                backlog[state]["dollars"] += total_tp
                backlog[state]["sq_ft"] += total_sq_ft

                if state == "Complete":
                    continue

                if state == "In Progress":
                    start_date = parse_date(r["first_template_date"] or "")
                else:
                    start_date = parse_date(r["est_start_month"] or "")
                    unscheduled_jobs.append(
                        {
                            "bid_id": r["bid_id"],
                            "bid_name": r["bid_name"] or "",
                            "project_manager": r["project_manager"] or "",
                            "dollars": total_tp,
                            "sq_ft": total_sq_ft,
                            "est_start_month": (r["est_start_month"] or "").strip(),
                        }
                    )

                start_month = month_floor(start_date.strftime("%Y-%m-%d")) if start_date else ""
                if start_month in horizon_set and start_date and start_date >= now.date():
                    if state == "In Progress":
                        monthly[start_month]["start_confirmed_dollars"] += total_tp
                        monthly[start_month]["start_confirmed_sq_ft"] += total_sq_ft
                    else:
                        monthly[start_month]["start_estimated_dollars"] += total_tp
                        monthly[start_month]["start_estimated_sq_ft"] += total_sq_ft
                elif start_date and start_date > window_end_dt.date():
                    if state == "In Progress":
                        plus_90["start_confirmed_dollars"] += total_tp
                        plus_90["start_confirmed_sq_ft"] += total_sq_ft
                    else:
                        plus_90["start_estimated_dollars"] += total_tp
                        plus_90["start_estimated_sq_ft"] += total_sq_ft

            needs_sync = []
            for r in needs_sync_rows:
                needs_sync.append(
                    {
                        "bid_id": r["bid_id"],
                        "bid_name": r["bid_name"] or "",
                        "project_manager": r["project_manager"] or "",
                        "reason": "Missing Moraware link"
                        if not (r["moraware_job_id"] or "").strip()
                        else "Missing Moraware status",
                    }
                )

            return {
                "pipeline_forecast": {
                    "backlog": backlog,
                    "window_start": window_start,
                    "window_end": window_end,
                    "forecast_months": horizon_months,
                    "monthly_forecast": monthly,
                    "unscheduled_jobs": unscheduled_jobs,
                    "plus_90": plus_90,
                },
                "completed_history": self.get_pm_completed_history(limit=12),
                "needs_sync": needs_sync,
            }

    def get_pm_monthly_report(self, year: int, month: int, project_manager: str = "", job_type: str = ""):
        """Return monthly PM report rows for jobs with complete invoice phases in the selected month."""
        year = int(year)
        month = int(month)
        month_start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            month_end = f"{year + 1:04d}-01-01"
        else:
            month_end = f"{year:04d}-{month + 1:02d}-01"

        with self._conn() as conn:
            params = [month_start, month_end]
            sql = """
                SELECT b.id AS bid_id,
                       b.bid_name,
                       b.project_manager,
                       b.est_complete_date,
                       b.moraware_job_date,
                       wc.name AS won_customer_name,
                       COALESCE(SUM(i.tp_code), 0) AS report_total,
                       COALESCE(SUM(i.sq_ft), 0) AS report_sq_ft,
                       COUNT(*) AS complete_phase_count
                FROM bids b
                JOIN invoice_data i ON i.bid_id = b.id
                LEFT JOIN customers wc ON wc.id = b.won_customer_id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND LOWER(TRIM(COALESCE(i.invoice_status, ''))) = 'complete'
                  AND NULLIF(TRIM(i.invoice_date), '') IS NOT NULL
                  AND i.invoice_date >= ?
                  AND i.invoice_date < ?
            """
            if project_manager:
                sql += " AND b.project_manager = ?"
                params.append(project_manager)
            sql += """
                GROUP BY b.id
                ORDER BY b.bid_name COLLATE NOCASE
            """
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

        job_type_map = self.get_pm_job_type()
        for row in rows:
            row["job_type"] = job_type_map.get(row["bid_id"], "Unassigned")

        if job_type:
            rows = [r for r in rows if r["job_type"] == job_type]
        return rows

    def get_pm_report_years(self):
        """Return year list for monthly PM reports (based on complete invoice dates)."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT strftime('%Y', i.invoice_date) AS yr
                FROM invoice_data i
                JOIN bids b ON b.id = i.bid_id
                WHERE b.status = 'WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                  AND LOWER(TRIM(COALESCE(i.invoice_status, ''))) = 'complete'
                  AND NULLIF(TRIM(i.invoice_date), '') IS NOT NULL
                ORDER BY yr
                """
            ).fetchall()
            return [r["yr"] for r in rows if r["yr"]]

    def get_salespersons(self):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT salesperson FROM bids WHERE salesperson IS NOT NULL AND salesperson != '' ORDER BY salesperson COLLATE NOCASE"
            ).fetchall()
            return [r["salesperson"] for r in rows]

    def get_project_managers(self):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT project_manager FROM bids WHERE project_manager IS NOT NULL AND project_manager != '' ORDER BY project_manager COLLATE NOCASE"
            ).fetchall()
            return [r["project_manager"] for r in rows]

    def get_awarded_years(self):
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT DISTINCT strftime('%Y', COALESCE(won_date, original_bid_date)) AS yr
                   FROM bids
                   WHERE status='WON' AND COALESCE(exclude_from_rollups, 0)=0
                   ORDER BY yr"""
            ).fetchall()
            return [r["yr"] for r in rows if r["yr"]]

    def move_bid_back_to_bidding(self, bid_id: int):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET status='PENDING', won_customer_id=NULL,
                   salesperson=NULL, project_manager=NULL,
                   moraware_job_date=NULL, won_date=NULL, won_notes=NULL, moraware_job_id=NULL,
                   moraware_job_number=NULL,
                   est_complete_date=NULL, est_complete_date_manual=0,
                   est_start_month=NULL, moraware_created_date=NULL,
                   parent_bid_id=NULL, bid_role='normal', exclude_from_rollups=0
                   WHERE id=?""",
                (bid_id,),
            )
            conn.execute("DELETE FROM invoice_data WHERE bid_id=?", (bid_id,))
            conn.execute("DELETE FROM bid_moraware_links WHERE bid_id=?", (bid_id,))
            conn.execute("DELETE FROM bid_moraware_allocations WHERE bid_id=?", (bid_id,))

    def set_moraware_job_id(self, bid_id: int, job_id: str, job_number: str = None):
        self.add_bid_moraware_link(
            bid_id,
            str(job_id or "").strip(),
            (job_number or "").strip() if job_number is not None else "",
            make_primary=True,
        )

    def set_moraware_job_number(self, bid_id: int, job_number: str):
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE bid_moraware_links
                SET moraware_job_number=?, updated_at=datetime('now')
                WHERE bid_id=? AND is_primary=1
                """,
                ((job_number or "").strip(), bid_id),
            )
            conn.execute(
                "UPDATE bids SET moraware_job_number=? WHERE id=?",
                (job_number, bid_id),
            )

    def set_moraware_job_status(self, bid_id: int, status: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bids SET moraware_job_status=?, last_moraware_sync_at=datetime('now') WHERE id=?",
                (status, bid_id),
            )

    def set_moraware_sync_timestamp(self, bid_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bids SET last_moraware_sync_at=datetime('now') WHERE id=?",
                (bid_id,),
            )

    def set_moraware_created_date(self, bid_id: int, created_date: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bids SET moraware_created_date=? WHERE id=?",
                ((created_date or "").strip(), bid_id),
            )
            self._reconcile_won_date_with_moraware_created(conn, bid_id)

    def refresh_bid_moraware_metadata(
        self,
        bid_id: int,
        job_number: str = "",
        created_date: str = "",
        salesperson: str = "",
        project_manager: str = "",
    ):
        """
        Refresh linked bid metadata from Moraware without wiping local values when
        Moraware omits a field. If Date Won is blank, backfill from created_date.
        """
        job_number = (job_number or "").strip()
        created_date = (created_date or "").strip()
        salesperson = (salesperson or "").strip()
        project_manager = (project_manager or "").strip()

        with self._conn() as conn:
            conn.execute(
                """
                UPDATE bids
                SET moraware_job_number = CASE WHEN ? = '' THEN moraware_job_number ELSE ? END,
                    moraware_created_date = CASE WHEN ? = '' THEN moraware_created_date ELSE ? END,
                    salesperson = CASE WHEN ? = '' THEN salesperson ELSE ? END,
                    project_manager = CASE WHEN ? = '' THEN project_manager ELSE ? END,
                    won_date = CASE
                        WHEN NULLIF(TRIM(COALESCE(won_date, '')), '') IS NULL
                             AND NULLIF(TRIM(?), '') IS NOT NULL
                        THEN ?
                        ELSE won_date
                    END
                WHERE id = ?
                """,
                (
                    job_number, job_number,
                    created_date, created_date,
                    salesperson, salesperson,
                    project_manager, project_manager,
                    created_date, created_date,
                    bid_id,
                ),
            )
            self._reconcile_won_date_with_moraware_created(conn, bid_id)

    def set_bid_sales_team(self, bid_id: int, salesperson: str = "", project_manager: str = ""):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bids SET salesperson=?, project_manager=? WHERE id=?",
                ((salesperson or "").strip(), (project_manager or "").strip(), bid_id),
            )

    def ensure_bid_won_for_link(
        self,
        bid_id: int,
        won_customer_id: int | None,
        salesperson: str = "",
        project_manager: str = "",
        won_notes: str = "",
        won_date: str = None,
    ):
        """
        Ensure a bid is WON before/while linking to Moraware.
        - If bid is already WON: no-op.
        - If bid is not WON: requires explicit won_customer_id.
        """
        with self._conn() as conn:
            row = conn.execute("SELECT status FROM bids WHERE id=?", (bid_id,)).fetchone()
        if not row:
            raise ValueError("Bid not found.")
        if str(row["status"] or "").strip().upper() == "WON":
            return
        if not won_customer_id:
            raise ValueError("A winning account must be selected before linking this bid.")
        self.mark_bid_won(
            bid_id,
            int(won_customer_id),
            salesperson=(salesperson or "").strip(),
            project_manager=(project_manager or "").strip(),
            won_notes=(won_notes or "").strip(),
            won_date=won_date,
        )

    def unsync_bid_from_moraware(self, bid_id: int):
        """
        Unsync Moraware link/invoice data while preserving WON/PENDING status.
        """
        with self._conn() as conn:
            conn.execute("DELETE FROM bid_moraware_links WHERE bid_id=?", (bid_id,))
            conn.execute("DELETE FROM bid_moraware_allocations WHERE bid_id=?", (bid_id,))
            conn.execute(
                "UPDATE bids SET moraware_job_id=NULL, moraware_job_number=NULL, moraware_job_status=NULL, last_moraware_sync_at=NULL WHERE id=?",
                (bid_id,),
            )
            conn.execute("DELETE FROM invoice_data WHERE bid_id=?", (bid_id,))

    def clear_moraware_job_id(self, bid_id: int):
        self.unsync_bid_from_moraware(bid_id)

    def get_won_bids_with_moraware_id(self):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT b.id, b.bid_name,
                           l.moraware_job_id,
                           COALESCE(NULLIF(TRIM(l.moraware_job_number), ''), b.moraware_job_number, '') AS moraware_job_number
                    FROM bids b
                    JOIN bid_moraware_links l ON l.bid_id = b.id AND l.is_primary = 1
                    WHERE b.status='WON'
                      AND COALESCE(b.exclude_from_rollups, 0)=0
                      AND NULLIF(TRIM(COALESCE(l.moraware_job_id, '')), '') IS NOT NULL
                    """
                ).fetchall()
            ]

    def get_won_bids_with_moraware_links(self):
        """Return WON bids with all linked Moraware jobs and primary metadata mirrored."""
        with self._conn() as conn:
            bid_rows = conn.execute(
                """
                SELECT b.id, b.bid_name, b.moraware_job_id, b.moraware_job_number
                FROM bids b
                WHERE b.status='WON'
                  AND COALESCE(b.exclude_from_rollups, 0)=0
                ORDER BY b.id
                """
            ).fetchall()
            out = []
            for row in bid_rows:
                bid = dict(row)
                links = conn.execute(
                    """
                    SELECT moraware_job_id, moraware_job_number, is_primary
                    FROM bid_moraware_links
                    WHERE bid_id=?
                    ORDER BY is_primary DESC, id ASC
                    """,
                    (bid["id"],),
                ).fetchall()
                bid["moraware_links"] = [dict(r) for r in links]
                if not bid["moraware_links"] and (bid.get("moraware_job_id") or "").strip():
                    bid["moraware_links"] = [
                        {
                            "moraware_job_id": (bid.get("moraware_job_id") or "").strip(),
                            "moraware_job_number": (bid.get("moraware_job_number") or "").strip(),
                            "is_primary": 1,
                        }
                    ]
                out.append(bid)
            return out

    def get_bids_for_customer(self, customer_id: int, date_from="", date_to=""):
        """Return all bids linked to a customer with latest revision data."""
        with self._conn() as conn:
            sql = """
                SELECT b.id, b.bid_name, b.estimator, b.original_bid_date,
                       CASE
                           WHEN b.status = 'WON' AND COALESCE(b.won_customer_id, 0) != ? THEN 'BIDDING'
                           ELSE b.status
                       END AS status,
                       r.bid_total, r.revision_no,
                       r.solid_surf_sf, r.stone_sf
                FROM bids b
                JOIN bid_customers bc ON bc.bid_id = b.id
                LEFT JOIN (
                    SELECT br.bid_id, br.bid_total, br.revision_no,
                           br.solid_surf_sf, br.stone_sf
                    FROM bid_revisions br
                    INNER JOIN (
                        SELECT bid_id, MAX(revision_no) AS max_rev
                        FROM bid_revisions GROUP BY bid_id
                    ) latest ON br.bid_id = latest.bid_id AND br.revision_no = latest.max_rev
                ) r ON r.bid_id = b.id
                WHERE bc.customer_id = ?
                  AND COALESCE(b.bid_role, 'normal') != 'parent'
            """
            params = [customer_id, customer_id]
            if date_from:
                sql += " AND b.original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND b.original_bid_date <= ?"
                params.append(date_to)
            sql += " ORDER BY b.original_bid_date ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
