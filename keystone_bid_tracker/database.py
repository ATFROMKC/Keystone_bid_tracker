"""
Keystone Bid Tracker - Database Layer
All SQLite CRUD operations for bids, customers, revisions.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime

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
            """)

            new_columns = [
                ("bids", "salesperson", "TEXT"),
                ("bids", "project_manager", "TEXT"),
                ("bids", "moraware_job_date", "TEXT"),
                ("bids", "won_notes", "TEXT"),
                ("bids", "moraware_job_id", "TEXT"),
                ("bids", "moraware_job_status", "TEXT"),
                ("bids", "last_moraware_sync_at", "TEXT"),
                ("invoice_data", "sq_ft", "REAL"),
                ("invoice_data", "template_date", "TEXT"),
                ("invoice_data", "install_date", "TEXT"),
                ("invoice_data", "contact_customer_date", "TEXT"),
                ("invoice_data", "contact_customer_notes", "TEXT"),
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
                CREATE INDEX IF NOT EXISTS idx_invoice_data_bid_id ON invoice_data(bid_id);
                CREATE INDEX IF NOT EXISTS idx_bid_revisions_bid_id_revision_no ON bid_revisions(bid_id, revision_no);
            """)

            conn.execute(
                "UPDATE bids SET status='PENDING' WHERE status IN ('LOST', 'DEAD')"
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
                "UPDATE bids SET won_customer_id = ? WHERE won_customer_id = ?",
                (merge_into_id, merge_from_id),
            )
            conn.execute(
                "DELETE FROM customers WHERE id = ?",
                (merge_from_id,),
            )

    # ------------------------------------------------------------------
    # Bids
    # ------------------------------------------------------------------
    def add_bid(self, bid_name: str, estimator: str, original_bid_date: str,
                notes: str, customer_ids: list, bid_total: float,
                solid_surf_sf: float = 0, stone_sf: float = 0) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO bids (bid_name, estimator, original_bid_date, notes)
                   VALUES (?, ?, ?, ?)""",
                (bid_name.strip(), estimator.strip(), original_bid_date, notes),
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
                   original_bid_date: str, notes: str, customer_ids: list):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET bid_name=?, estimator=?, original_bid_date=?, notes=?
                   WHERE id=?""",
                (bid_name.strip(), estimator.strip(), original_bid_date, notes, bid_id),
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
    def mark_bid_won(self, bid_id: int, won_customer_id: int,
                     salesperson: str = "", project_manager: str = "",
                     moraware_job_date: str = "", won_notes: str = ""):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET status='WON', won_customer_id=?,
                   salesperson=?, project_manager=?, moraware_job_date=?, won_notes=?
                   WHERE id=?""",
                (won_customer_id, salesperson, project_manager,
                 moraware_job_date, won_notes, bid_id),
            )

    def update_won_details(self, bid_id: int, won_customer_id: int,
                           salesperson: str = "", project_manager: str = "",
                           moraware_job_date: str = "", won_notes: str = ""):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET won_customer_id=?,
                   salesperson=?, project_manager=?, moraware_job_date=?, won_notes=?
                   WHERE id=?""",
                (won_customer_id, salesperson, project_manager,
                 moraware_job_date, won_notes, bid_id),
            )

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
                            WHEN SUM(CASE WHEN invoice_status='Complete' THEN 1 ELSE 0 END) = COUNT(*) THEN 'Invoiced'
                            WHEN SUM(CASE WHEN invoice_status='Complete' THEN 1 ELSE 0 END) > 0 THEN 'Partial'
                            ELSE 'Pending'
                        END AS invoice_status_calc
                    FROM invoice_data GROUP BY bid_id
                ) inv ON inv.bid_id = b.id
                WHERE b.status = 'WON'
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
                sql += " AND strftime('%Y', COALESCE(b.moraware_job_date, b.original_bid_date)) = ?"
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

            sql += " ORDER BY COALESCE(b.moraware_job_date, b.original_bid_date) ASC, b.id ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_awarded_stats(self):
        with self._conn() as conn:
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM bids WHERE status='WON'"
            ).fetchone()
            total_awarded = count_row["cnt"] if count_row else 0

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
                WHERE b.status = 'WON'
            """).fetchone()
            total_won_value = value_row["total_value"] if value_row else 0

            inv_row = conn.execute("""
                SELECT COALESCE(SUM(id2.tp_code), 0) AS total_invoiced
                FROM invoice_data id2
                JOIN bids b ON b.id = id2.bid_id
                WHERE b.status = 'WON' AND id2.invoice_status = 'Complete'
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
                    "SELECT * FROM invoice_data WHERE bid_id=? ORDER BY phase",
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
                       (bid_id, phase, tp_code, sq_ft, invoice_date, template_date,
                        install_date, contact_customer_date, contact_customer_notes,
                        invoice_status, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        bid_id,
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
                """SELECT DISTINCT strftime('%Y', COALESCE(moraware_job_date, original_bid_date)) AS yr
                   FROM bids WHERE status='WON' ORDER BY yr"""
            ).fetchall()
            return [r["yr"] for r in rows if r["yr"]]

    def move_bid_back_to_bidding(self, bid_id: int):
        with self._conn() as conn:
            conn.execute(
                """UPDATE bids SET status='PENDING', won_customer_id=NULL,
                   salesperson=NULL, project_manager=NULL,
                   moraware_job_date=NULL, won_notes=NULL, moraware_job_id=NULL
                   WHERE id=?""",
                (bid_id,),
            )
            conn.execute("DELETE FROM invoice_data WHERE bid_id=?", (bid_id,))

    def set_moraware_job_id(self, bid_id: int, job_id: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bids SET moraware_job_id=? WHERE id=?",
                (job_id, bid_id),
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

    def clear_moraware_job_id(self, bid_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE bids SET moraware_job_id=NULL, moraware_job_status=NULL, last_moraware_sync_at=NULL WHERE id=?",
                (bid_id,),
            )
            conn.execute("DELETE FROM invoice_data WHERE bid_id=?", (bid_id,))

    def get_won_bids_with_moraware_id(self):
        with self._conn() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    """SELECT id, bid_name, moraware_job_id FROM bids
                       WHERE status='WON' AND moraware_job_id IS NOT NULL AND moraware_job_id != ''"""
                ).fetchall()
            ]

    def get_bids_for_customer(self, customer_id: int, date_from="", date_to=""):
        """Return all bids linked to a customer with latest revision data."""
        with self._conn() as conn:
            sql = """
                SELECT b.id, b.bid_name, b.estimator, b.original_bid_date,
                       b.status, r.bid_total, r.revision_no,
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
            """
            params = [customer_id]
            if date_from:
                sql += " AND b.original_bid_date >= ?"
                params.append(date_from)
            if date_to:
                sql += " AND b.original_bid_date <= ?"
                params.append(date_to)
            sql += " ORDER BY b.original_bid_date ASC"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
