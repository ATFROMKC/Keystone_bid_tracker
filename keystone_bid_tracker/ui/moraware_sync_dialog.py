"""
Keystone Bid Tracker - Moraware Sync Dialog
Fuzzy-matches bids to Moraware jobs. Two scan modes: unawarded only or all.
Matches grouped by confidence: Strong (85%+), Possible (60-84%), No Match (<60%).
Review dialog shows side-by-side comparison; Confirm Won reuses MarkWonDialog.
"""

import logging
import re
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QProgressBar, QAbstractItemView, QRadioButton, QGroupBox,
    QFrame, QButtonGroup, QComboBox, QLineEdit, QListWidget,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QColor

from thefuzz import fuzz

from config import get_config
from ui.mark_won_dialog import MarkWonDialog

logger = logging.getLogger("moraware_sync")

STRONG_THRESHOLD = 85
MATCH_THRESHOLD = 75
DISPLAY_THRESHOLD = 65

ROW_COLORS = {
    "strong": QColor(26, 58, 26),
    "possible": QColor(58, 52, 16),
    "none": QColor(42, 42, 42),
}


class _ManualSearchWorker(QThread):
    """Search Moraware jobs live from ManualSyncDialog."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, client, query):
        super().__init__()
        self.client = client
        self.query = query

    def run(self):
        try:
            url = (
                f"{self.client.base_url}/sys/jobs?"
                "pagesize=1000"
                "&cols=JA13,CN1,JN1,JA77,JN5"
                "&sort=a2"
            )
            resp = self.client.session.get(url, timeout=30)
            resp.raise_for_status()

            def _norm(text):
                t = (text or "").lower().strip()
                t = re.sub(r"[^a-z0-9]+", " ", t)
                return re.sub(r"\s+", " ", t).strip()

            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("tbody#JobsBody tr")
            if not rows:
                rows = soup.select("#JobsBody tr")

            name_col = num_col = account_col = sp_col = pm_col = -1
            for row in rows:
                header_cells = row.select(
                    "td.headerSortableCol, th.headerSortableCol, "
                    "td.headerCol, th.headerCol"
                )
                if header_cells:
                    all_cells = row.select("td, th")
                    for i, c in enumerate(all_cells):
                        norm = _norm(c.get_text(strip=True))
                        if norm == "job number":
                            num_col = i
                        elif norm == "account":
                            account_col = i
                        elif norm == "job name":
                            name_col = i
                        elif norm in ("salesperson", "sales person", "sales rep"):
                            sp_col = i
                        elif norm == "keystone pm":
                            pm_col = i
                    break

            jobs = []
            for row in rows:
                cells = row.select("td")
                if len(cells) < 3:
                    continue
                if any(cls in (c.get("class") or [])
                       for c in cells
                       for cls in ("headerSortableCol", "headerCol")):
                    continue

                link = (cells[name_col].select_one("a[href*='/sys/job/']")
                        if 0 <= name_col < len(cells) else None)
                if not link:
                    for cell in cells:
                        link = cell.select_one("a[href*='/sys/job/']")
                        if link:
                            break
                if not link:
                    continue

                href = link.get("href", "")
                parts = href.rstrip("/").split("/")
                job_id = parts[-1] if parts else ""
                name = link.get_text(strip=True)
                job_number = (cells[num_col].get_text(strip=True)
                              if 0 <= num_col < len(cells) else "")
                account_cell = (cells[account_col]
                                if 0 <= account_col < len(cells) else None)
                account = ""
                if account_cell:
                    acc_link = account_cell.select_one("a[href*='/sys/account/']")
                    account = (acc_link.get_text(strip=True) if acc_link
                               else account_cell.get_text(strip=True))
                salesperson = (cells[sp_col].get_text(strip=True)
                               if 0 <= sp_col < len(cells) else "").strip()
                project_manager = (cells[pm_col].get_text(strip=True)
                                   if 0 <= pm_col < len(cells) else "").strip()

                if job_id and name:
                    jobs.append({
                        "id": job_id,
                        "name": name,
                        "job_number": job_number,
                        "account": account,
                        "salesperson": salesperson,
                        "project_manager": project_manager,
                    })

            logger.info("Manual search: fetched %d total jobs", len(jobs))
            q = self.query.strip().lower()
            filtered = [
                j for j in jobs
                if q in j["name"].lower() or q in j["job_number"].lower()
            ]
            logger.info("Manual search: %d jobs match query '%s'", len(filtered), self.query)
            self.finished.emit(filtered)
        except Exception as e:
            logger.error("Manual search failed: %s", e)
            self.error.emit(str(e))


class _ManualDetailWorker(QThread):
    """Fetch job details + invoice data in background for ManualSyncDialog."""
    finished = pyqtSignal(str, dict)

    def __init__(self, job_id, client):
        super().__init__()
        self.job_id = job_id
        self.client = client

    def run(self):
        result = {}
        try:
            details = self.client.get_job_details(self.job_id)
            if details:
                result["created_date"] = details.get("created_date", "")
        except Exception as e:
            logger.warning("ManualSync: failed to fetch details for %s: %s", self.job_id, e)

        try:
            invoice_data = self.client.get_invoice_data(self.job_id)
            codes = [p["tp_code"] for p in invoice_data if p.get("tp_code") is not None]
            if codes:
                result["job_ticket_a"] = sum(codes)
            sq_fts = [p["sq_ft"] for p in invoice_data if p.get("sq_ft") is not None]
            if sq_fts:
                result["sq_ft"] = sum(sq_fts)
        except Exception as e:
            logger.warning("ManualSync: failed to fetch invoice data for %s: %s", self.job_id, e)

        self.finished.emit(self.job_id, result)


class ManualSyncDialog(QDialog):
    """Search and manually link a bid to a Moraware job."""

    LINK_ONLY = "link_only"
    LINK_AND_WON = "link_and_won"
    CANCELLED = "cancelled"

    def __init__(self, bid, moraware_jobs, db, client=None, parent=None):
        super().__init__(parent)
        self.bid = bid
        self.moraware_jobs = moraware_jobs
        self.db = db
        self.moraware_client = client
        self.result_action = self.CANCELLED
        self._selected_job = None

        self.setWindowTitle(f"Manual Sync — {bid.get('bid_name', '')}")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        left = QGroupBox("Local Bid")
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(6)
        self._add_field(left_layout, "Bid Name", self.bid.get("bid_name", ""))
        self._add_field(left_layout, "Bid Date", self._fmt(self.bid.get("original_bid_date", "")))
        bid_total = self.bid.get("bid_total") or 0
        self._add_field(left_layout, "Bid Total", f"${bid_total:,.2f}" if bid_total else "—")
        stone_sf = self.bid.get("stone_sf") or 0
        solid_sf = self.bid.get("solid_surf_sf") or 0
        self._add_field(left_layout, "Stone SF", f"{stone_sf:,.0f}" if stone_sf else "—")
        self._add_field(left_layout, "Solid SF", f"{solid_sf:,.0f}" if solid_sf else "—")
        self._add_field(left_layout, "Status", self.bid.get("status", ""))
        self._add_field(left_layout, "Accounts", self.bid.get("customer_names", "") or "—")
        left_layout.addStretch()
        columns.addWidget(left)

        right = QGroupBox("Find Moraware Job")
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(8)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by job name or job #...")
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)
        right_layout.addLayout(search_row)

        self._search_status = QLabel("")
        self._search_status.setObjectName("secondaryLabel")
        self._search_status.hide()
        right_layout.addWidget(self._search_status)
        self._search_worker = None

        self.job_list = QListWidget()
        self.job_list.currentItemChanged.connect(self._on_job_selected)
        right_layout.addWidget(self.job_list, 1)

        self._detail_box = QGroupBox("Job Details")
        detail_layout = QVBoxLayout(self._detail_box)
        detail_layout.setSpacing(4)
        self._detail_labels = {}
        for key in ("Job #", "Account", "Salesperson", "Keystone PM",
                     "Created Date", "Job Ticket A", "Sq Ft"):
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setObjectName("secondaryLabel")
            k.setFixedWidth(110)
            row.addWidget(k)
            v = QLabel("—")
            v.setWordWrap(True)
            row.addWidget(v, 1)
            detail_layout.addLayout(row)
            self._detail_labels[key] = v
        self._detail_box.hide()
        self._detail_worker = None
        right_layout.addWidget(self._detail_box)

        columns.addWidget(right)
        layout.addLayout(columns, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.link_btn = QPushButton("Link Only")
        self.link_btn.setEnabled(False)
        self.link_btn.clicked.connect(self._on_link_only)
        btn_row.addWidget(self.link_btn)

        self.link_won_btn = QPushButton("Link && Confirm Won")
        self.link_won_btn.setObjectName("successButton")
        self.link_won_btn.setEnabled(False)
        self.link_won_btn.clicked.connect(self._on_link_and_won)
        btn_row.addWidget(self.link_won_btn)

        layout.addLayout(btn_row)

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        if not self.moraware_client:
            self._search_status.setText("No Moraware client available.")
            self._search_status.show()
            return
        self.job_list.clear()
        self._selected_job = None
        self._detail_box.hide()
        self.link_btn.setEnabled(False)
        self.link_won_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self._search_status.setText("Searching...")
        self._search_status.show()

        self._search_worker = _ManualSearchWorker(self.moraware_client, query)
        self._search_worker.finished.connect(self._on_search_results)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_search_results(self, jobs):
        self.search_btn.setEnabled(True)
        self.job_list.clear()
        for job in jobs:
            name = job.get("name", "")
            num = job.get("job_number", "")
            account = job.get("account", "")
            display = f"#{num} — {name}"
            if account:
                display += f" ({account})"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, job)
            self.job_list.addItem(item)
        self._search_status.setText(f"Found {len(jobs)} job(s).")

    def _on_search_error(self, error_msg):
        self.search_btn.setEnabled(True)
        self._search_status.setText(f"Search failed: {error_msg}")

    def _on_job_selected(self, current, _previous):
        if not current:
            self._selected_job = None
            self._detail_box.hide()
            self.link_btn.setEnabled(False)
            self.link_won_btn.setEnabled(False)
            return
        job = current.data(Qt.UserRole)
        self._selected_job = job
        self._job_details = None
        self._detail_labels["Job #"].setText(job.get("job_number", "—"))
        self._detail_labels["Account"].setText(job.get("account", "") or "—")
        self._detail_labels["Salesperson"].setText(job.get("salesperson", "") or "—")
        self._detail_labels["Keystone PM"].setText(job.get("project_manager", "") or "—")
        self._detail_labels["Created Date"].setText("Loading...")
        self._detail_labels["Job Ticket A"].setText("Loading...")
        self._detail_labels["Sq Ft"].setText("Loading...")
        self._detail_box.show()
        self.link_btn.setEnabled(True)
        self.link_won_btn.setEnabled(True)
        self._fetch_job_details(job["id"])

    def _fetch_job_details(self, job_id):
        if not self.moraware_client:
            self._detail_labels["Created Date"].setText("—")
            self._detail_labels["Job Ticket A"].setText("—")
            self._detail_labels["Sq Ft"].setText("—")
            return
        self._detail_worker = _ManualDetailWorker(job_id, self.moraware_client)
        self._detail_worker.finished.connect(self._on_details_fetched)
        self._detail_worker.start()

    def _on_details_fetched(self, job_id, result):
        if not self._selected_job or self._selected_job["id"] != job_id:
            return
        created = result.get("created_date", "")
        self._detail_labels["Created Date"].setText(self._fmt(created) if created else "—")

        tp = result.get("job_ticket_a")
        self._detail_labels["Job Ticket A"].setText(f"${tp:,.2f}" if tp is not None else "—")

        sq = result.get("sq_ft")
        self._detail_labels["Sq Ft"].setText(f"{sq:,.0f}" if sq is not None else "—")

        self._job_details = result

    def _on_link_only(self):
        if not self._selected_job:
            return
        self.db.set_moraware_job_id(self.bid["id"], self._selected_job["id"])
        self.result_action = self.LINK_ONLY
        self.accept()

    def _on_link_and_won(self):
        if not self._selected_job:
            return
        job = self._selected_job
        bid_id = self.bid["id"]
        job_id = job["id"]

        self.db.set_moraware_job_id(bid_id, job_id)

        won_dlg = MarkWonDialog(self.db, bid_id, parent=self)

        sp = job.get("salesperson", "")
        pm = job.get("project_manager", "")
        if sp:
            idx = won_dlg.salesperson_input.findText(sp, Qt.MatchFixedString)
            if idx >= 0:
                won_dlg.salesperson_input.setCurrentIndex(idx)
            else:
                won_dlg.salesperson_input.addItem(sp)
                won_dlg.salesperson_input.setCurrentText(sp)
        if pm:
            idx = won_dlg.pm_input.findText(pm, Qt.MatchFixedString)
            if idx >= 0:
                won_dlg.pm_input.setCurrentIndex(idx)
            else:
                won_dlg.pm_input.addItem(pm)
                won_dlg.pm_input.setCurrentText(pm)

        if won_dlg.exec_() and won_dlg.selected_customer_id:
            salesperson = won_dlg.salesperson or sp
            project_manager = won_dlg.project_manager or pm
            moraware_job_date = won_dlg.moraware_job_date or ""
            self.db.mark_bid_won(
                bid_id, won_dlg.selected_customer_id,
                salesperson=salesperson,
                project_manager=project_manager,
                moraware_job_date=moraware_job_date,
                won_notes=won_dlg.won_notes,
            )

        self.result_action = self.LINK_AND_WON
        self.accept()

    @staticmethod
    def _add_field(layout, label, value):
        row = QHBoxLayout()
        key = QLabel(f"{label}:")
        key.setObjectName("secondaryLabel")
        key.setFixedWidth(110)
        row.addWidget(key)
        val = QLabel(str(value))
        val.setWordWrap(True)
        row.addWidget(val, 1)
        layout.addLayout(row)

    @staticmethod
    def _fmt(date_str):
        if not date_str:
            return ""
        try:
            from datetime import datetime
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%m/%d/%Y")
        except (ValueError, TypeError):
            return date_str


class ReviewMatchDialog(QDialog):
    """Side-by-side comparison of a local bid and a Moraware job."""

    CONFIRM_WON = "confirm_won"
    NOT_A_MATCH = "not_a_match"
    SKIP = "skip"

    def __init__(self, bid, job, score, db, moraware_client=None, parent=None):
        super().__init__(parent)
        self.bid = bid
        self.job = job
        self.score = score
        self.db = db
        self.moraware_client = moraware_client
        self.result_action = self.SKIP
        self._job_details = None

        self.setWindowTitle("Review Match")
        self.setMinimumSize(700, 420)
        self.setModal(True)
        self._build_ui()
        self._fetch_job_details()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        if self.score >= STRONG_THRESHOLD:
            color = "#4caf50"
            label = "Strong Match"
        elif self.score >= MATCH_THRESHOLD:
            color = "#ff9800"
            label = "Possible Match"
        else:
            color = "#666666"
            label = "No Match"

        score_lbl = QLabel(f"{self.score}% — {label}")
        score_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {color};"
        )
        score_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(score_lbl)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        left = QGroupBox("Local Bid")
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(6)
        self._add_field(left_layout, "Bid Name", self.bid.get("bid_name", ""))
        self._add_field(left_layout, "Bid Date", self._fmt(self.bid.get("original_bid_date", "")))
        bid_total = self.bid.get("bid_total") or 0
        self._add_field(left_layout, "Bid Total", f"${bid_total:,.2f}" if bid_total else "—")
        stone_sf = self.bid.get("stone_sf") or 0
        solid_sf = self.bid.get("solid_surf_sf") or 0
        self._add_field(left_layout, "Stone SF", f"{stone_sf:,.0f}" if stone_sf else "—")
        self._add_field(left_layout, "Solid SF", f"{solid_sf:,.0f}" if solid_sf else "—")
        self._add_field(left_layout, "Status", self.bid.get("status", ""))
        self._add_field(left_layout, "Accounts", self.bid.get("customer_names", "") or "—")
        left_layout.addStretch()
        columns.addWidget(left)

        right = QGroupBox("Moraware Job")
        self._right_layout = QVBoxLayout(right)
        self._right_layout.setSpacing(6)
        self._add_field(self._right_layout, "Job Name", self.job.get("name", ""))
        job_num = self.job.get("job_number", self.job.get("id", ""))
        self._add_field(self._right_layout, "Job #", job_num)
        self._add_field(self._right_layout, "Account", self.job.get("account", "") or "—")
        self._detail_fields_start = self._right_layout.count()
        self._add_field(self._right_layout, "Created Date", "Loading...")
        self._add_field(self._right_layout, "Salesperson", "Loading...")
        self._add_field(self._right_layout, "Keystone PM", "Loading...")
        self._add_field(self._right_layout, "Job Ticket A", "Loading...")
        self._add_field(self._right_layout, "Sq Ft", "Loading...")
        self._right_layout.addStretch()
        columns.addWidget(right)

        self._tp_warning = QLabel("")
        self._tp_warning.setWordWrap(True)
        self._tp_warning.setStyleSheet(
            "color: #ff9800; font-weight: bold; padding: 6px 0;"
        )
        self._tp_warning.hide()

        self._acct_mismatch_frame = QFrame()
        acct_row = QHBoxLayout(self._acct_mismatch_frame)
        acct_row.setContentsMargins(0, 0, 0, 0)
        acct_row.setSpacing(8)
        self._acct_mismatch_label = QLabel("")
        self._acct_mismatch_label.setWordWrap(True)
        self._acct_mismatch_label.setStyleSheet(
            "color: #42a5f5; padding: 4px 0;"
        )
        acct_row.addWidget(self._acct_mismatch_label, 1)
        self._rename_btn = QPushButton("Rename to Match")
        self._rename_btn.setFixedWidth(140)
        self._rename_btn.clicked.connect(self._on_rename_account)
        acct_row.addWidget(self._rename_btn)
        self._acct_mismatch_frame.hide()
        self._rename_customer_id = None
        self._rename_target_name = None

        layout.addLayout(columns, 1)
        layout.addWidget(self._tp_warning)
        layout.addWidget(self._acct_mismatch_frame)

        self._check_account_mismatch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        skip_btn = QPushButton("Skip")
        skip_btn.clicked.connect(self._on_skip)
        btn_row.addWidget(skip_btn)

        not_match_btn = QPushButton("Not a Match")
        not_match_btn.setObjectName("dangerButton")
        not_match_btn.clicked.connect(self._on_not_match)
        btn_row.addWidget(not_match_btn)

        if self.score >= MATCH_THRESHOLD:
            confirm_btn = QPushButton("Confirm Won")
            confirm_btn.setObjectName("successButton")
            confirm_btn.clicked.connect(self._on_confirm_won)
            btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

    def _fetch_job_details(self):
        if not self.moraware_client:
            self._update_detail_fields("—", "—", "—", "—", "—")
            return
        try:
            details = self.moraware_client.get_job_details(self.job["id"])
            self._job_details = details
        except Exception as e:
            logger.warning("Failed to fetch job details for %s: %s", self.job["id"], e)
            details = None

        tp_total = None
        sq_ft_total = None
        try:
            invoice_data = self.moraware_client.get_invoice_data(self.job["id"])
            codes = [p["tp_code"] for p in invoice_data if p.get("tp_code") is not None]
            if codes:
                tp_total = sum(codes)
            sq_fts = [p["sq_ft"] for p in invoice_data if p.get("sq_ft") is not None]
            if sq_fts:
                sq_ft_total = sum(sq_fts)
        except Exception as e:
            logger.warning("Failed to fetch invoice data for %s: %s", self.job["id"], e)

        tp_str = f"${tp_total:,.2f}" if tp_total is not None else "—"
        sq_ft_str = f"{sq_ft_total:,.0f}" if sq_ft_total is not None else "—"

        if details:
            self._update_detail_fields(
                self._fmt(details.get("created_date", "")) or "—",
                details.get("salesperson", "") or "—",
                details.get("project_manager", "") or "—",
                tp_str,
                sq_ft_str,
            )
        else:
            self._update_detail_fields("—", "—", "—", tp_str, sq_ft_str)

        self._check_tp_warning(tp_total)

    def _check_tp_warning(self, tp_total):
        bid_total = self.bid.get("bid_total") or 0
        if tp_total is None or not bid_total:
            return
        diff = abs(tp_total - bid_total)
        pct = (diff / bid_total) * 100 if bid_total else 0
        if pct >= 20 or diff >= 5000:
            self._tp_warning.setText(
                f"\u26a0 Job Ticket A total (${tp_total:,.2f}) differs from "
                f"bid total (${bid_total:,.2f}) by ${diff:,.2f} ({pct:.0f}%)"
            )
            self._tp_warning.show()

    def _update_detail_fields(self, created, salesperson, pm, tp_code, sq_ft="—"):
        start = self._detail_fields_start
        for i, value in enumerate([created, salesperson, pm, tp_code, sq_ft]):
            idx = start + i
            item = self._right_layout.itemAt(idx)
            if item and item.layout():
                val_widget = item.layout().itemAt(1)
                if val_widget and val_widget.widget():
                    val_widget.widget().setText(value)

    @staticmethod
    def _add_field(layout, label, value):
        row = QHBoxLayout()
        key = QLabel(f"{label}:")
        key.setObjectName("secondaryLabel")
        key.setFixedWidth(110)
        row.addWidget(key)
        val = QLabel(str(value))
        val.setWordWrap(True)
        row.addWidget(val, 1)
        layout.addLayout(row)

    @staticmethod
    def _fmt(date_str):
        if not date_str:
            return ""
        try:
            from datetime import datetime
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%m/%d/%Y")
        except (ValueError, TypeError):
            return date_str

    def _check_account_mismatch(self):
        mw_account = (self.job.get("account") or "").strip()
        if not mw_account:
            return
        bid_customers = self.db.get_bid_customers(self.bid["id"])
        for c in bid_customers:
            local_name = c["name"].strip()
            if local_name.lower() == mw_account.lower():
                continue
            score = max(
                fuzz.token_sort_ratio(local_name, mw_account),
                fuzz.token_set_ratio(local_name, mw_account),
                fuzz.partial_ratio(local_name.lower(), mw_account.lower()),
            )
            if 70 <= score < 100:
                self._rename_customer_id = c["id"]
                self._rename_target_name = mw_account
                self._acct_mismatch_label.setText(
                    f"\U0001f504 Local account \"{local_name}\" is similar to "
                    f"Moraware account \"{mw_account}\" — consider renaming to match."
                )
                self._acct_mismatch_frame.show()
                return

    def _on_rename_account(self):
        if not self._rename_customer_id or not self._rename_target_name:
            return
        existing = self.db.get_customer_by_name(self._rename_target_name)
        if existing and existing["id"] != self._rename_customer_id:
            reply = QMessageBox.question(
                self, "Account Exists",
                f"An account named \"{self._rename_target_name}\" already exists.\n"
                f"Merge into it instead?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.db.merge_customers(self._rename_customer_id, existing["id"])
                self._acct_mismatch_label.setText("Merged successfully.")
                self._rename_btn.hide()
            return
        self.db.update_customer(self._rename_customer_id, self._rename_target_name)
        self._acct_mismatch_label.setText(
            f"Renamed to \"{self._rename_target_name}\"."
        )
        self._acct_mismatch_label.setStyleSheet("color: #4caf50; padding: 4px 0;")
        self._rename_btn.hide()

    def _on_skip(self):
        self.result_action = self.SKIP
        self.reject()

    def _on_not_match(self):
        self.result_action = self.NOT_A_MATCH
        self.accept()

    def _on_confirm_won(self):
        self.result_action = self.CONFIRM_WON
        self.accept()


class FetchJobsWorker(QThread):
    """Background thread to log in and fetch job list from Moraware."""
    finished = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def __init__(self, base_url, username, password, active_only=True):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.active_only = active_only

    def run(self):
        try:
            from utils.moraware_client import MorewareClient
            client = MorewareClient(self.username, self.password, self.base_url)
            client.login()

            def _norm(text):
                t = (text or "").lower().strip()
                t = re.sub(r"[^a-z0-9]+", " ", t)
                return re.sub(r"\s+", " ", t).strip()

            status_filter = "&filters=2|3:0:j19:10:j19;3,5;1" if self.active_only else ""
            jobs_url = (
                f"{client.base_url}/sys/jobs?"
                "pagesize=300"
                "&cols=JA13,CN1,JN1,JA77,JN5"
                "&sort=a2"
                f"{status_filter}"
            )
            logger.info("Fetching jobs from %s", jobs_url)
            resp = client.session.get(jobs_url, timeout=30)
            resp.raise_for_status()
            logger.debug("Jobs page loaded (%d bytes)", len(resp.text))

            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            rows = soup.select("tbody#JobsBody tr")
            if not rows:
                rows = soup.select("#JobsBody tr")
            logger.info("Job list: found %d candidate rows", len(rows))

            name_col = num_col = account_col = sp_col = pm_col = -1
            for row in rows:
                header_cells = row.select("td.headerSortableCol, th.headerSortableCol, td.headerCol, th.headerCol")
                if header_cells:
                    all_cells = row.select("td, th")
                    header_texts = []
                    for i, c in enumerate(all_cells):
                        norm = _norm(c.get_text(strip=True))
                        header_texts.append(norm)
                        if norm == "job number":
                            num_col = i
                        elif norm == "account":
                            account_col = i
                        elif norm == "job name":
                            name_col = i
                        elif norm in ("salesperson", "sales person", "sales rep"):
                            sp_col = i
                        elif norm == "keystone pm":
                            pm_col = i
                    logger.info("Header texts: %s", header_texts)
                    logger.info(
                        "Column indices: num=%d, name=%d, account=%d, sp=%d, pm=%d",
                        num_col, name_col, account_col, sp_col, pm_col,
                    )
                    break

            for row in rows:
                cells = row.select("td")
                if len(cells) < 3:
                    continue

                if cells[0].select("td.headerSortableCol, td.headerCol") or \
                   any("headerSortableCol" in (c.get("class") or []) for c in cells) or \
                   any("headerCol" in (c.get("class") or []) for c in cells):
                    continue

                link = cells[name_col].select_one("a[href*='/sys/job/']") if 0 <= name_col < len(cells) else None
                if not link:
                    for cell in cells:
                        link = cell.select_one("a[href*='/sys/job/']")
                        if link:
                            break
                if not link:
                    continue

                href = link.get("href", "")
                parts = href.rstrip("/").split("/")
                job_id = parts[-1] if parts else ""
                name = link.get_text(strip=True)

                job_number = cells[num_col].get_text(strip=True) if 0 <= num_col < len(cells) else ""

                account_cell = cells[account_col] if 0 <= account_col < len(cells) else None
                account = ""
                if account_cell:
                    acc_link = account_cell.select_one("a[href*='/sys/account/']")
                    account = acc_link.get_text(strip=True) if acc_link else account_cell.get_text(strip=True)

                salesperson = (cells[sp_col].get_text(strip=True) if 0 <= sp_col < len(cells) else "").strip()
                project_manager = (cells[pm_col].get_text(strip=True) if 0 <= pm_col < len(cells) else "").strip()

                if job_id and name:
                    jobs.append({
                        "id": job_id,
                        "name": name,
                        "job_number": job_number,
                        "account": account,
                        "salesperson": salesperson,
                        "project_manager": project_manager,
                    })

            logger.info("Parsed %d Moraware jobs from page", len(jobs))
            self.finished.emit(jobs, client)
        except Exception as e:
            logger.error("Fetch failed: %s", e)
            self.error.emit(str(e))


class MorewareSyncDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.moraware_jobs = []
        self.moraware_client = None
        self.matches = []
        self._dismissed = set()
        self.setWindowTitle("Moraware Sync")
        self.setMinimumSize(1200, 680)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Moraware Job Sync")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        desc = QLabel(
            "Match local bids to Moraware jobs using fuzzy name matching. "
            "Review each match and confirm won bids."
        )
        desc.setObjectName("secondaryLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # --- Bids filter ---
        bids_row = QHBoxLayout()
        bids_row.setSpacing(16)

        self.radio_unawarded = QRadioButton("Scan unawarded bids only")
        self.radio_unawarded.setChecked(True)
        self.radio_all = QRadioButton("Scan all bids")

        self.scan_group = QButtonGroup(self)
        self.scan_group.addButton(self.radio_unawarded)
        self.scan_group.addButton(self.radio_all)

        bids_row.addWidget(self.radio_unawarded)
        bids_row.addWidget(self.radio_all)
        bids_row.addStretch()
        layout.addLayout(bids_row)

        # --- Jobs filter ---
        jobs_row = QHBoxLayout()
        jobs_row.setSpacing(16)

        jobs_row.addWidget(QLabel("Moraware Jobs:"))

        self.jobs_active_rb = QRadioButton("Active jobs only")
        self.jobs_active_rb.setChecked(True)
        self.jobs_all_rb = QRadioButton("All jobs")

        self.jobs_group = QButtonGroup(self)
        self.jobs_group.addButton(self.jobs_active_rb)
        self.jobs_group.addButton(self.jobs_all_rb)

        jobs_row.addWidget(self.jobs_active_rb)
        jobs_row.addWidget(self.jobs_all_rb)
        jobs_row.addStretch()

        self.fetch_btn = QPushButton("Fetch && Match")
        self.fetch_btn.setObjectName("primaryButton")
        self.fetch_btn.clicked.connect(self._on_fetch)
        jobs_row.addWidget(self.fetch_btn)

        layout.addLayout(jobs_row)

        # --- Moraware job filters (populated after fetch) ---
        mw_filt_row = QHBoxLayout()
        mw_filt_row.setSpacing(12)

        mw_filt_row.addWidget(QLabel("Salesperson:"))
        self.sp_filter = QComboBox()
        self.sp_filter.addItem("All")
        self.sp_filter.setMinimumWidth(140)
        mw_filt_row.addWidget(self.sp_filter)

        mw_filt_row.addSpacing(8)
        mw_filt_row.addWidget(QLabel("Keystone PM:"))
        self.pm_filter = QComboBox()
        self.pm_filter.addItem("All")
        self.pm_filter.setMinimumWidth(140)
        mw_filt_row.addWidget(self.pm_filter)

        mw_filt_row.addSpacing(8)
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self._on_filter_changed)
        mw_filt_row.addWidget(self.apply_filters_btn)

        mw_filt_row.addStretch()
        layout.addLayout(mw_filt_row)

        # --- Progress / status ---
        self.progress = QProgressBar()
        self.progress.setMaximum(0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        layout.addWidget(self.status_label)

        # --- Match table ---
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Bid Name", "Status", "Bid Total", "Moraware Job", "Job #",
            "Salesperson", "Keystone PM", "Match %", "Synced", "Action",
        ])
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.setColumnWidth(9, 160)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        layout.addWidget(self.table, 1)

        # --- Bottom buttons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.manual_sync_btn = QPushButton("Manual Sync")
        self.manual_sync_btn.setEnabled(False)
        self.manual_sync_btn.clicked.connect(self._on_manual_sync)
        btn_row.addWidget(self.manual_sync_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_filtered_bids(self) -> list:
        bids = self.db.get_bids()
        if self.radio_unawarded.isChecked():
            return [b for b in bids if b.get("status", "").upper() != "WON"]
        return bids

    # ------------------------------------------------------------------
    # Fetch & Match
    # ------------------------------------------------------------------
    def _on_fetch(self):
        cfg = get_config()
        username = cfg.get("moraware_username", "")
        password = cfg.get("moraware_password", "")
        base_url = cfg.get("moraware_url", "")

        if not all([username, password, base_url]):
            QMessageBox.warning(
                self, "Moraware Not Configured",
                "Moraware credentials are not set.\n"
                "Go to Settings to configure your Moraware URL, username, and password."
            )
            return

        self.fetch_btn.setEnabled(False)
        self.progress.show()
        self.status_label.setText("Fetching jobs from Moraware...")

        self.worker = FetchJobsWorker(base_url, username, password,
                                       active_only=self.jobs_active_rb.isChecked())
        self.worker.finished.connect(self._on_jobs_fetched)
        self.worker.error.connect(self._on_fetch_error)
        self.worker.start()

    @staticmethod
    def _fuzzy_score(name_a: str, name_b: str) -> int:
        return max(
            fuzz.token_sort_ratio(name_a, name_b),
            fuzz.token_set_ratio(name_a, name_b),
            fuzz.partial_ratio(name_a, name_b),
        )

    @staticmethod
    def _customer_boost(bid_customers_str: str, job_name: str) -> int:
        if not bid_customers_str:
            return 0
        customers = [c.strip() for c in bid_customers_str.split(",") if c.strip()]
        best = 0
        for cust in customers:
            score = max(
                fuzz.token_set_ratio(cust, job_name),
                fuzz.partial_ratio(cust.lower(), job_name.lower()),
            )
            if score > best:
                best = score
        if best >= 70:
            return 15
        return 0

    def _on_jobs_fetched(self, jobs, client):
        self.progress.hide()
        self.fetch_btn.setEnabled(True)
        self.moraware_jobs = jobs
        self.moraware_client = client
        self._dismissed.clear()

        self._populate_mw_filters(jobs)
        self._run_matching()

    def _populate_mw_filters(self, jobs):
        self.sp_filter.blockSignals(True)
        self.pm_filter.blockSignals(True)

        self.sp_filter.clear()
        self.sp_filter.addItem("All")
        self.pm_filter.clear()
        self.pm_filter.addItem("All")

        sp_set = sorted({(j.get("salesperson") or "").strip() for j in jobs if (j.get("salesperson") or "").strip()})
        pm_set = sorted({(j.get("project_manager") or "").strip() for j in jobs if (j.get("project_manager") or "").strip()})
        for sp in sp_set:
            self.sp_filter.addItem(sp)
        for pm in pm_set:
            self.pm_filter.addItem(pm)

        self.sp_filter.blockSignals(False)
        self.pm_filter.blockSignals(False)

    def _get_filtered_mw_jobs(self):
        jobs = self.moraware_jobs
        sp = self.sp_filter.currentText()
        if sp and sp != "All":
            jobs = [j for j in jobs if j.get("salesperson") == sp]
        pm = self.pm_filter.currentText()
        if pm and pm != "All":
            jobs = [j for j in jobs if j.get("project_manager") == pm]
        return jobs

    def _on_filter_changed(self):
        if self.moraware_jobs:
            self._dismissed.clear()
            self._run_matching()

    def _run_matching(self):
        bids = self._get_filtered_bids()
        jobs = self._get_filtered_mw_jobs()
        self.matches = []

        for bid in bids:
            bid_name = bid["bid_name"]
            bid_customers = bid.get("customer_names") or ""

            best_job = None
            best_score = 0

            for job in jobs:
                name_score = self._fuzzy_score(bid_name, job["name"])
                boost = self._customer_boost(bid_customers, job["name"])
                total = min(name_score + boost, 100)
                if total > best_score:
                    best_score = total
                    best_job = job

            if best_job and best_score >= DISPLAY_THRESHOLD:
                self.matches.append({
                    "bid": bid,
                    "job": best_job,
                    "score": best_score,
                })

        self.matches.sort(key=lambda m: m["score"], reverse=True)
        self._populate_table()

        scan_mode = "unawarded" if self.radio_unawarded.isChecked() else "all"
        strong = sum(1 for m in self.matches if m["score"] >= STRONG_THRESHOLD)
        possible = sum(1 for m in self.matches if MATCH_THRESHOLD <= m["score"] < STRONG_THRESHOLD)
        filtered_jobs = len(jobs)
        total_jobs = len(self.moraware_jobs)
        job_text = f"{filtered_jobs} of {total_jobs}" if filtered_jobs != total_jobs else str(total_jobs)
        self.status_label.setText(
            f"Scanning {job_text} Moraware jobs against {len(bids)} {scan_mode} bids: "
            f"{strong} strong, {possible} possible matches."
        )

    def _on_fetch_error(self, error_msg):
        self.progress.hide()
        self.fetch_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Fetch Error", f"Failed to fetch Moraware jobs:\n{error_msg}")

    # ------------------------------------------------------------------
    # Match table
    # ------------------------------------------------------------------
    def _populate_table(self):
        visible = [m for i, m in enumerate(self.matches) if i not in self._dismissed]
        self.table.setRowCount(len(visible))

        for row, m in enumerate(visible):
            bid = m["bid"]
            score = m["score"]

            synced = bool(bid.get("moraware_job_id"))

            if score >= STRONG_THRESHOLD:
                bg = ROW_COLORS["strong"]
            elif score >= MATCH_THRESHOLD:
                bg = ROW_COLORS["possible"]
            else:
                bg = ROW_COLORS["none"]

            def make_item(text, align=Qt.AlignLeft | Qt.AlignVCenter):
                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setBackground(bg)
                return item

            name_item = make_item(bid["bid_name"])
            name_item.setData(Qt.UserRole, bid["id"])
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, make_item(bid["status"], Qt.AlignCenter))

            bid_total = bid.get("bid_total") or 0
            total_str = f"${bid_total:,.2f}" if bid_total else ""
            self.table.setItem(row, 2, make_item(total_str, Qt.AlignRight | Qt.AlignVCenter))

            self.table.setItem(row, 3, make_item(m["job"]["name"]))
            self.table.setItem(row, 4, make_item(
                m["job"].get("job_number", ""), Qt.AlignCenter))

            self.table.setItem(row, 5, make_item(m["job"].get("salesperson", "")))
            self.table.setItem(row, 6, make_item(m["job"].get("project_manager", "")))

            self.table.setItem(row, 7, make_item(f"{score}%", Qt.AlignCenter))

            if synced:
                lbl = QLabel("✓")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("color: #4caf50; font-size: 16px; font-weight: bold;")
                self.table.setCellWidget(row, 8, lbl)

            review_btn = QPushButton("Review")
            review_btn.setObjectName("primaryButton")
            match_idx = self.matches.index(m)
            review_btn.clicked.connect(lambda checked, idx=match_idx: self._on_review(idx))
            self.table.setCellWidget(row, 9, review_btn)

        self.table.sortByColumn(7, Qt.DescendingOrder)

    # ------------------------------------------------------------------
    # Selection & Manual Sync
    # ------------------------------------------------------------------
    def _on_table_selection_changed(self):
        self.manual_sync_btn.setEnabled(len(self.table.selectedItems()) > 0)

    def _on_manual_sync(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        visual_row = selected_rows[0].row()
        bid_id = self.table.item(visual_row, 0).data(Qt.UserRole)
        match = next((m for m in self.matches if m["bid"]["id"] == bid_id), None)
        if not match:
            return
        bid = match["bid"]

        dlg = ManualSyncDialog(
            bid, self.moraware_jobs, self.db,
            client=self.moraware_client, parent=self,
        )
        dlg.exec_()

        if dlg.result_action != ManualSyncDialog.CANCELLED:
            self._populate_table()
            action = "linked" if dlg.result_action == ManualSyncDialog.LINK_ONLY else "linked & marked WON"
            self.status_label.setText(
                f"'{bid['bid_name']}' {action} to Moraware job."
            )

    # ------------------------------------------------------------------
    # Review & Confirm
    # ------------------------------------------------------------------
    def _on_review(self, match_idx):
        m = self.matches[match_idx]
        bid = m["bid"]
        job = m["job"]

        dlg = ReviewMatchDialog(
            bid, job, m["score"], self.db,
            moraware_client=self.moraware_client,
            parent=self,
        )
        dlg.exec_()

        if dlg.result_action == ReviewMatchDialog.CONFIRM_WON:
            self._do_confirm_won(bid, job, match_idx, dlg._job_details)
        elif dlg.result_action == ReviewMatchDialog.NOT_A_MATCH:
            self._dismissed.add(match_idx)
            self._populate_table()
            self.status_label.setText(f"Dismissed match for '{bid['bid_name']}'.")

    @staticmethod
    def _parse_moraware_date(date_str):
        """Try multiple date formats Moraware might return."""
        if not date_str:
            return None
        date_str = date_str.strip().split("T")[0]
        for fmt in ("yyyy-MM-dd", "MM/dd/yyyy", "M/d/yyyy", "yyyy/MM/dd"):
            d = QDate.fromString(date_str, fmt)
            if d.isValid():
                return d
        return None

    @staticmethod
    def _set_combo_text(combo, text):
        """Set combo text, adding the value as an item if not already present."""
        if not text:
            return
        idx = combo.findText(text, Qt.MatchFixedString)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.addItem(text)
            combo.setCurrentText(text)

    def _do_confirm_won(self, bid, job, match_idx, job_details):
        bid_id = bid["id"]
        job_id = job["id"]

        won_dlg = MarkWonDialog(self.db, bid_id, parent=self)

        if job_details:
            created = job_details.get("created_date", "")
            d = self._parse_moraware_date(created)
            if d:
                won_dlg.date_edit.setDate(d)
            self._set_combo_text(won_dlg.salesperson_input, job_details.get("salesperson", ""))
            self._set_combo_text(won_dlg.pm_input, job_details.get("project_manager", ""))

        if won_dlg.exec_() and won_dlg.selected_customer_id:
            salesperson = won_dlg.salesperson or (
                job_details.get("salesperson", "") if job_details else ""
            )
            project_manager = won_dlg.project_manager or (
                job_details.get("project_manager", "") if job_details else ""
            )
            moraware_job_date = won_dlg.moraware_job_date or (
                job_details.get("created_date", "") if job_details else ""
            )
            self.db.mark_bid_won(
                bid_id, won_dlg.selected_customer_id,
                salesperson=salesperson,
                project_manager=project_manager,
                moraware_job_date=moraware_job_date,
                won_notes=won_dlg.won_notes,
            )
            self.db.set_moraware_job_id(bid_id, job_id)

            self._dismissed.add(match_idx)
            self._populate_table()
            self.status_label.setText(
                f"'{bid['bid_name']}' marked WON and linked to Moraware job {job['name']}."
            )
