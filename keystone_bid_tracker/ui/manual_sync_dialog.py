"""
Keystone Bid Tracker - Manual Sync Dialog
Standalone dialog to search Moraware jobs and link a bid.
Handles its own login and search via background workers.
"""

import logging
import re

from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from config import get_config
from ui.mark_won_dialog import MarkWonDialog

logger = logging.getLogger("manual_sync")


def _parse_jobs(html):
    """Parse Moraware jobs list HTML and return list of job dicts."""
    def _norm(text):
        t = (text or "").lower().strip()
        t = re.sub(r"[^a-z0-9]+", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    soup = BeautifulSoup(html, "html.parser")
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

    return jobs


def _parse_jobs_from_rows(rows_or_soup):
    """Parse job dicts from rows or a BeautifulSoup object."""
    if hasattr(rows_or_soup, 'select'):
        rows = rows_or_soup.select("tbody#JobsBody tr")
        if not rows:
            rows = rows_or_soup.select("#JobsBody tr")
    else:
        rows = rows_or_soup
    def _norm(text):
        t = (text or "").lower().strip()
        t = re.sub(r"[^a-z0-9]+", " ", t)
        return re.sub(r"\s+", " ", t).strip()

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

    return jobs


class _LoginWorker(QThread):
    """Log in to Moraware in background."""
    success = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, base_url, username, password):
        super().__init__()
        self.base_url = base_url
        self.username = username
        self.password = password

    def run(self):
        try:
            from utils.moraware_client import MorewareClient
            client = MorewareClient(self.username, self.password, self.base_url)
            client.login()
            self.success.emit(client)
        except Exception as e:
            logger.error("Login failed: %s", e)
            self.error.emit(str(e))


def _norm_jobnum(val):
    return re.sub(r'[#\s]', '', str(val or "")).strip()


class _MWSearchWorker(QThread):
    """Smart Moraware job search with early-exit optimizations."""
    progress = pyqtSignal(str)
    partial = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, client, query, job_cache=None):
        super().__init__()
        self.client = client
        self.query = query
        self.job_cache = job_cache if job_cache is not None else []

    def _filter_cache(self, cache, query):
        q_raw = query.strip()
        q_lower = q_raw.lower()
        q_digits = re.sub(r'[#\s]', '', q_raw)
        job_number_mode = q_digits.isdigit() and len(q_digits) >= 4

        if job_number_mode:
            return [j for j in cache
                    if _norm_jobnum(j.get("job_number")) == q_digits]
        results = []
        for j in cache:
            name = str(j.get("name", "")).lower()
            account = str(j.get("account", "")).lower()
            if name == q_lower:
                return [{**j}]
            elif name.startswith(q_lower):
                results.append((3, {**j}))
            elif q_lower in name:
                results.append((2, {**j}))
            elif q_lower in account:
                results.append((1, {**j}))
        results.sort(key=lambda x: -x[0])
        return [j for _, j in results]

    def run(self):
        try:
            base_url = (
                f"{self.client.base_url}/sys/jobs"
                f"?view=0&status=0&pagesize=300"
                f"&cols=JA13,CN1,JN1,JA77,JN5"
                f"&sort=a2"
            )

            q_raw = self.query.strip()
            q_lower = q_raw.lower()
            q_digits = re.sub(r'[#\s]', '', q_raw)
            job_number_mode = q_digits.isdigit() and len(q_digits) >= 4

            if self.job_cache:
                results = self._filter_cache(self.job_cache, self.query)
                if results:
                    self.progress.emit(
                        f"Found {len(results)} from cache "
                        f"({len(self.job_cache)} jobs cached)")
                    self.finished.emit(results)
                    return
                self.progress.emit(
                    f"Nothing in cache ({len(self.job_cache)} jobs) "
                    f"— searching Moraware...")

            cache_was_empty = len(self.job_cache) == 0

            def fingerprint(jobs):
                if not jobs:
                    return None
                return (
                    str(jobs[0].get("job_number", "")).strip(),
                    str(jobs[-1].get("job_number", "")).strip(),
                )

            def norm_jobnum(val):
                return _norm_jobnum(val)

            def is_login_page(html):
                return 'name="user"' in html and 'name="pwd"' in html

            if job_number_mode:
                self._search_by_number(base_url, q_digits, fingerprint,
                                       norm_jobnum, is_login_page,
                                       cache_was_empty)
            else:
                self._search_by_name(base_url, q_lower, fingerprint,
                                     is_login_page, cache_was_empty)

        except Exception as e:
            logger.error("Search failed: %s", e)
            self.error.emit(str(e))

    def _search_by_number(self, base_url, q_digits, fingerprint,
                          norm_jobnum, is_login_page, cache_was_empty):
        prefix = ("Cache empty" if cache_was_empty else "Cache miss")
        prefix += " — searching Moraware..."
        self.progress.emit(prefix)

        prev_fp = None
        for page in range(1, 200):
            if self.isInterruptionRequested():
                return
            resp = self.client.session.get(
                f"{base_url}&page={page}", timeout=30)
            if is_login_page(resp.text):
                self.error.emit("Session expired — please close and reopen")
                return
            jobs = _parse_jobs_from_rows(
                BeautifulSoup(resp.text, "html.parser"))
            if not jobs:
                break
            self.job_cache.extend(
                j for j in jobs
                if j.get("job_number") not in
                {c.get("job_number") for c in self.job_cache})
            fp = fingerprint(jobs)
            if fp == prev_fp:
                self.error.emit(
                    "Pagination stuck — Moraware not advancing pages")
                return
            prev_fp = fp
            if self.isInterruptionRequested():
                return
            match = next(
                (j for j in jobs
                 if norm_jobnum(j.get("job_number")) == q_digits),
                None,
            )
            if match:
                self.finished.emit([match])
                return
            self.progress.emit(f"{prefix} page {page}")
            if len(jobs) < 300 and page > 1:
                break
        self.finished.emit([])

    def _search_by_name(self, base_url, q_lower, fingerprint, is_login_page,
                        cache_was_empty):
        prefix = ("Cache empty" if cache_was_empty else "Cache miss")
        prefix += " — searching Moraware..."
        self.progress.emit(prefix)

        matches = []
        MAX_STRONG = 25
        MAX_PAGES = 65
        prev_fp = None
        hit_limit = False
        page = 0

        for page in range(1, MAX_PAGES + 1):
            if self.isInterruptionRequested():
                return
            resp = self.client.session.get(
                f"{base_url}&page={page}", timeout=30)
            if is_login_page(resp.text):
                self.error.emit("Session expired — please close and reopen")
                return
            jobs = _parse_jobs_from_rows(
                BeautifulSoup(resp.text, "html.parser"))
            if not jobs:
                break
            self.job_cache.extend(
                j for j in jobs
                if j.get("job_number") not in
                {c.get("job_number") for c in self.job_cache})
            fp = fingerprint(jobs)
            if fp == prev_fp:
                self.error.emit("Pagination stuck")
                return
            prev_fp = fp
            if self.isInterruptionRequested():
                return

            for j in jobs:
                name = str(j.get("name", "")).lower().strip()
                account = str(j.get("account", "")).lower().strip()
                if name == q_lower:
                    self.finished.emit([{**j}])
                    return
                elif name.startswith(q_lower):
                    matches.append((3, {**j}))
                elif q_lower in name:
                    matches.append((2, {**j}))
                elif q_lower in account:
                    matches.append((1, {**j}))

            strong_count = sum(1 for score, _ in matches if score >= 2)
            self.progress.emit(
                f"{prefix} page {page} ({len(matches)} matches so far)")

            if strong_count >= MAX_STRONG:
                hit_limit = True
                break
            if len(jobs) < 300 and page > 1:
                break

        if hit_limit or page >= MAX_PAGES:
            self.partial.emit(
                f"Showing partial results ({len(matches)} found)"
                f" — refine your search")

        seen = set()
        results = []
        for score, j in sorted(matches, key=lambda x: -x[0]):
            jid = j.get("id")
            if jid not in seen:
                seen.add(jid)
                results.append(j)

        self.finished.emit(results)


class ManualSyncDialog(QDialog):
    """Standalone dialog to search and link a bid to a Moraware job."""

    def __init__(self, bid, db, job_cache=None, parent=None):
        super().__init__(parent)
        self.bid = bid
        self.db = db
        self._job_cache = job_cache if job_cache is not None else []
        self._client = None
        self._selected_job = None
        self._login_worker = None
        self._search_worker = None

        print(f"DEBUG bid: {bid}")
        self.setWindowTitle(f"Sync with Moraware — {bid.get('bid_name', '')}")
        self.setMinimumSize(750, 520)
        self.setModal(True)
        self._build_ui()
        self._start_login()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        left = QGroupBox("Local Bid")
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(6)
        self._add_field(left_layout, "Bid Name", self.bid.get("bid_name") or "—")
        self._add_field(left_layout, "Bid Date", self.bid.get("original_bid_date") or "—")
        self._add_field(left_layout, "Bid Total", f"${self.bid.get('bid_total') or 0:,.2f}")
        self._add_field(left_layout, "Stone SF", str(self.bid.get("stone_sf") or "—"))
        self._add_field(left_layout, "Solid SF", str(self.bid.get("solid_surf_sf") or "—"))
        self._add_field(left_layout, "Status", self.bid.get("status") or "—")
        self._add_field(left_layout, "Accounts", self.bid.get("customer_names") or "—")
        left_layout.addStretch()
        columns.addWidget(left)

        right = QGroupBox("Find Moraware Job")
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(8)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by job name or job #...")
        self.search_input.setEnabled(False)
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)
        self.search_btn = QPushButton("Search")
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)
        self.cancel_search_btn = QPushButton("Cancel")
        self.cancel_search_btn.clicked.connect(self._on_cancel_search)
        self.cancel_search_btn.hide()
        search_row.addWidget(self.cancel_search_btn)
        right_layout.addLayout(search_row)

        self._status_label = QLabel("Connecting...")
        self._status_label.setObjectName("secondaryLabel")
        right_layout.addWidget(self._status_label)

        self._partial_label = QLabel("")
        self._partial_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        self._partial_label.setWordWrap(True)
        self._partial_label.hide()
        right_layout.addWidget(self._partial_label)

        self.job_list = QListWidget()
        self.job_list.currentItemChanged.connect(self._on_job_selected)
        right_layout.addWidget(self.job_list, 1)

        self._detail_box = QGroupBox("Job Details")
        detail_layout = QVBoxLayout(self._detail_box)
        detail_layout.setSpacing(4)
        self._detail_labels = {}
        for key in ("Job #", "Account", "Salesperson", "Keystone PM"):
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
        right_layout.addWidget(self._detail_box)

        columns.addWidget(right)
        layout.addLayout(columns, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.unlink_btn = QPushButton("Unlink")
        self.unlink_btn.setVisible(bool(self.bid.get("moraware_job_id")))
        self.unlink_btn.clicked.connect(self._on_unlink)
        btn_row.addWidget(self.unlink_btn)

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

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def _start_login(self):
        cfg = get_config()
        url = cfg.get("moraware_url", "")
        user = cfg.get("moraware_username", "")
        pw = cfg.get("moraware_password", "")
        if not all([url, user, pw]):
            self._status_label.setText(
                "Moraware credentials not configured. Go to Settings.")
            return
        self._login_worker = _LoginWorker(url, user, pw)
        self._login_worker.success.connect(self._on_login_success)
        self._login_worker.error.connect(self._on_login_error)
        self._login_worker.start()

    def _on_login_success(self, client):
        self._client = client
        self.search_input.setEnabled(True)
        self.search_btn.setEnabled(True)
        self._status_label.setText("Ready — enter a search term above.")
        self.search_input.setFocus()

    def _on_login_error(self, error_msg):
        self._status_label.setText(f"Login failed: {error_msg}")
        self._status_label.setStyleSheet("color: #ef5350;")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def _on_search(self):
        query = self.search_input.text().strip()
        if not query or not self._client:
            return
        self.job_list.clear()
        self._selected_job = None
        self._detail_box.hide()
        self.link_btn.setEnabled(False)
        self.link_won_btn.setEnabled(False)
        self.search_input.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.cancel_search_btn.show()
        self._partial_label.hide()
        self._status_label.setStyleSheet("")
        self._status_label.setText("Searching...")

        self._search_worker = _MWSearchWorker(
            self._client, query, job_cache=self._job_cache)
        self._search_worker.progress.connect(self._on_search_progress)
        self._search_worker.partial.connect(self._on_search_partial)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.start()

    def _on_cancel_search(self):
        if self._search_worker and self._search_worker.isRunning():
            self._search_worker.requestInterruption()
        self._enable_search_controls()
        self._status_label.setText("Search cancelled.")
        self.cancel_search_btn.hide()

    def _on_search_progress(self, message):
        self._status_label.setText(message)

    def _on_search_partial(self, message):
        self._partial_label.setText(message)
        self._partial_label.show()

    def _on_search_error(self, error_msg):
        self._status_label.setText(error_msg)
        self._status_label.setStyleSheet("color: #ef5350;")
        self._enable_search_controls()
        self.cancel_search_btn.hide()

    def _on_search_finished(self, jobs):
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
        self._status_label.setStyleSheet("")
        self._status_label.setText(f"Found {len(jobs)} job(s).")
        self._enable_search_controls()
        self.cancel_search_btn.hide()

    def _enable_search_controls(self):
        self.search_input.setEnabled(True)
        self.search_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Job selection
    # ------------------------------------------------------------------
    def _on_job_selected(self, current, _previous):
        if not current:
            self._selected_job = None
            self._detail_box.hide()
            self.link_btn.setEnabled(False)
            self.link_won_btn.setEnabled(False)
            return
        job = current.data(Qt.UserRole)
        self._selected_job = job
        self._detail_labels["Job #"].setText(job.get("job_number", "—"))
        self._detail_labels["Account"].setText(job.get("account", "") or "—")
        self._detail_labels["Salesperson"].setText(
            job.get("salesperson", "") or "—")
        self._detail_labels["Keystone PM"].setText(
            job.get("project_manager", "") or "—")
        self._detail_box.show()
        self.link_btn.setEnabled(True)
        self.link_won_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_unlink(self):
        self.db.clear_moraware_job_id(self.bid["id"])
        self.accept()

    def _on_link_only(self):
        if not self._selected_job:
            return
        self.db.set_moraware_job_id(self.bid["id"], self._selected_job["id"])
        self.accept()

    def _on_link_and_won(self):
        if not self._selected_job:
            return
        job = self._selected_job
        bid_id = self.bid["id"]

        self.db.set_moraware_job_id(bid_id, job["id"])

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

        self.accept()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
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
