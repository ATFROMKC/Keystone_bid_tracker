"""
Keystone Bid Tracker - Awarded Jobs Tab
Shows WON bids with invoice tracking, Moraware sync, and detail expansion.
"""

import os
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QHeaderView, QFrame,
    QAbstractItemView, QMessageBox, QProgressDialog, QTextEdit, QDialog,
    QFormLayout, QDateEdit, QCheckBox, QMenu,
    QApplication,
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QColor

from config import get_config
from ui.mark_won_dialog import MarkWonDialog

class StatCard(QFrame):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(80)
        self.setMinimumWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.value_label)

        self.text_label = QLabel(label_text)
        self.text_label.setObjectName("statLabel")
        layout.addWidget(self.text_label)

    def set_value(self, val):
        self.value_label.setText(str(val))


class InvoiceSyncWorker(QThread):
    """Background thread to refresh linked Moraware invoice + metadata data."""
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int, int)
    error = pyqtSignal(str)

    def __init__(self, db, single_bid_id=None):
        super().__init__()
        self.db = db
        self.single_bid_id = single_bid_id

    def run(self):
        try:
            from utils.moraware_client import MorewareClient
            cfg = get_config()
            username = cfg.get("moraware_username", "")
            password = cfg.get("moraware_password", "")
            base_url = cfg.get("moraware_url", "")

            if not all([username, password, base_url]):
                self.error.emit("Moraware credentials not configured. Go to Settings.")
                return

            client = MorewareClient(username, password, base_url, use_fast_sync=True)
            client.login()

            if self.single_bid_id:
                bid = self.db.get_bid_by_id(self.single_bid_id)
                if not bid:
                    self.error.emit("Bid not found.")
                    return
                links = self.db.get_bid_moraware_links(self.single_bid_id)
                if not links:
                    self.error.emit("This bid has no Moraware Job ID linked.")
                    return

                linked_jobs = []
                primary_job_id = ""
                for link in links:
                    job_id = str((link or {}).get("moraware_job_id") or "").strip()
                    if not job_id:
                        continue
                    linked_jobs.append({"bid_id": self.single_bid_id, "moraware_job_id": job_id})
                    if not primary_job_id and int((link or {}).get("is_primary") or 0) == 1:
                        primary_job_id = job_id
                if not linked_jobs:
                    self.error.emit("This bid has no Moraware Job ID linked.")
                    return

                result = client.sync_invoice_data_fast(
                    linked_jobs=linked_jobs,
                    progress_cb=lambda i, total: self.progress.emit(i, total),
                )
                rows_by_job_id = result.get("rows_by_job_id", {}) or {}
                phases = []
                for link in links:
                    job_id = str((link or {}).get("moraware_job_id") or "").strip()
                    if not job_id:
                        continue
                    for row in (rows_by_job_id.get(job_id, []) or []):
                        payload = dict(row)
                        payload["moraware_job_id"] = job_id
                        phases.append(payload)
                self.db.upsert_invoice_data(self.single_bid_id, phases)

                if not primary_job_id:
                    primary_job_id = str((bid.get("moraware_job_id") or "")).strip()
                meta = (result.get("meta_by_job_id", {}) or {}).get(primary_job_id, {}) or {}
                job_status = (meta.get("status") or "").strip()
                if job_status in ("Active", "Complete"):
                    self.db.set_moraware_job_status(self.single_bid_id, job_status)
                else:
                    self.db.set_moraware_sync_timestamp(self.single_bid_id)

                self.db.refresh_bid_moraware_metadata(
                    self.single_bid_id,
                    job_number=(meta.get("job_number") or "").strip(),
                    created_date=(meta.get("created_date") or "").strip(),
                    salesperson=(meta.get("salesperson") or "").strip(),
                    project_manager=(meta.get("project_manager") or "").strip(),
                )
                self.finished.emit(1, len(phases))
            else:
                bids = self.db.get_won_bids_with_moraware_links()
                linked_jobs = []
                for b in bids:
                    for link in b.get("moraware_links") or []:
                        job_id = str((link or {}).get("moraware_job_id") or "").strip()
                        if not job_id:
                            continue
                        linked_jobs.append({"bid_id": b["id"], "moraware_job_id": job_id})

                result = client.sync_invoice_data_fast(
                    linked_jobs=linked_jobs,
                    progress_cb=lambda i, total: self.progress.emit(i, total),
                )
                rows_by_job_id = result.get("rows_by_job_id", {}) or {}
                meta_by_job_id = result.get("meta_by_job_id", {}) or {}

                total_phases = 0
                for b in bids:
                    links = b.get("moraware_links") or []
                    if not links:
                        continue
                    merged_phases = []
                    primary_job_id = ""
                    for link in links:
                        job_id = str((link or {}).get("moraware_job_id") or "").strip()
                        if not job_id:
                            continue
                        if not primary_job_id and int((link or {}).get("is_primary") or 0) == 1:
                            primary_job_id = job_id
                        job_rows = rows_by_job_id.get(job_id, []) or []
                        for row in job_rows:
                            payload = dict(row)
                            payload["moraware_job_id"] = job_id
                            merged_phases.append(payload)
                    if not primary_job_id:
                        primary_job_id = str(b.get("moraware_job_id") or "").strip()

                    self.db.upsert_invoice_data(b["id"], merged_phases)
                    total_phases += len(merged_phases)

                    meta = meta_by_job_id.get(primary_job_id, {}) or {}
                    job_status = (meta.get("status") or "").strip()
                    if job_status in ("Active", "Complete"):
                        self.db.set_moraware_job_status(b["id"], job_status)
                    else:
                        self.db.set_moraware_sync_timestamp(b["id"])

                    self.db.refresh_bid_moraware_metadata(
                        b["id"],
                        job_number=(meta.get("job_number") or "").strip(),
                        created_date=(meta.get("created_date") or "").strip(),
                        salesperson=(meta.get("salesperson") or "").strip(),
                        project_manager=(meta.get("project_manager") or "").strip(),
                    )
                self.finished.emit(len(bids), total_phases)

        except Exception as e:
            self.error.emit(str(e))


class PMEditJobDialog(QDialog):
    """PM-only Edit Job dialog (kept separate from MarkWonDialog)."""

    def __init__(self, db, bid_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.bid_id = bid_id
        self.bid = self.db.get_bid_by_id(bid_id)

        self.selected_customer_id = None
        self.salesperson = ""
        self.project_manager = ""
        self.won_date = ""
        self.moraware_job_date = ""
        self.won_notes = ""
        self.est_complete_date = None
        self.est_complete_date_manual = None
        self.est_start_month = None

        self.setWindowTitle("Edit Job")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(10)

        title = QLabel("Edit Job")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        bid_name = QLabel((self.bid or {}).get("bid_name") or "")
        bid_name.setObjectName("subheadingLabel")
        layout.addWidget(bid_name)

        form = QFormLayout()
        form.setSpacing(8)

        self.account_input = QComboBox()
        customers = self.db.get_bid_customers(self.bid_id)
        for customer in customers:
            self.account_input.addItem(customer["name"], customer["id"])
        won_customer_id = (self.bid or {}).get("won_customer_id")
        if won_customer_id:
            idx = self.account_input.findData(won_customer_id)
            if idx >= 0:
                self.account_input.setCurrentIndex(idx)
        form.addRow("Winning account:", self.account_input)

        self.salesperson_input = QComboBox()
        self.salesperson_input.setEditable(True)
        self.salesperson_input.setInsertPolicy(QComboBox.NoInsert)
        self.salesperson_input.addItem("")
        for sp in self.db.get_salespersons():
            self.salesperson_input.addItem(sp)
        self.salesperson_input.setCurrentText((self.bid or {}).get("salesperson") or "")
        form.addRow("Salesperson:", self.salesperson_input)

        self.pm_input = QComboBox()
        self.pm_input.setEditable(True)
        self.pm_input.setInsertPolicy(QComboBox.NoInsert)
        self.pm_input.addItem("")
        for pm in self.db.get_project_managers():
            self.pm_input.addItem(pm)
        self.pm_input.setCurrentText((self.bid or {}).get("project_manager") or "")
        form.addRow("Project manager:", self.pm_input)

        self.won_date_input = QDateEdit()
        self.won_date_input.setCalendarPopup(True)
        self.won_date_input.setDisplayFormat("MM/dd/yyyy")
        self.won_date_input.setDate(QDate.currentDate())
        existing_won_date = (self.bid or {}).get("won_date")
        if existing_won_date:
            won_date = QDate.fromString(existing_won_date, "yyyy-MM-dd")
            if won_date.isValid():
                self.won_date_input.setDate(won_date)
        form.addRow("Date won:", self.won_date_input)

        self.est_complete_manual_input = QCheckBox("Manually set estimated completion date")
        self.est_complete_date_input = QDateEdit()
        self.est_complete_date_input.setCalendarPopup(True)
        self.est_complete_date_input.setDisplayFormat("MM/dd/yyyy")
        self.est_complete_date_input.setDate(QDate.currentDate())
        existing_est_date = (self.bid or {}).get("est_complete_date")
        if existing_est_date:
            est_date = QDate.fromString(existing_est_date, "yyyy-MM-dd")
            if est_date.isValid():
                self.est_complete_date_input.setDate(est_date)

        manual_flag = int((self.bid or {}).get("est_complete_date_manual") or 0) == 1
        self.est_complete_manual_input.setChecked(manual_flag)
        self.est_complete_date_input.setEnabled(manual_flag)
        self.est_complete_manual_input.toggled.connect(self.est_complete_date_input.setEnabled)
        form.addRow(self.est_complete_manual_input)
        form.addRow("Est. complete date:", self.est_complete_date_input)

        self.est_start_month_manual_input = QCheckBox("Set estimated start month for not-started forecast")
        self.est_start_month_input = QDateEdit()
        self.est_start_month_input.setCalendarPopup(True)
        self.est_start_month_input.setDisplayFormat("MM/yyyy")
        self.est_start_month_input.setDate(QDate.currentDate())
        existing_start_month = (self.bid or {}).get("est_start_month")
        if existing_start_month:
            start_month = QDate.fromString(existing_start_month, "yyyy-MM-dd")
            if start_month.isValid():
                self.est_start_month_input.setDate(start_month)
        has_start_month = bool((existing_start_month or "").strip())
        self.est_start_month_manual_input.setChecked(has_start_month)
        self.est_start_month_input.setEnabled(has_start_month)
        self.est_start_month_manual_input.toggled.connect(self.est_start_month_input.setEnabled)
        form.addRow(self.est_start_month_manual_input)
        form.addRow("Est. start month:", self.est_start_month_input)

        self.won_notes_input = QTextEdit()
        self.won_notes_input.setMaximumHeight(80)
        self.won_notes_input.setPlainText((self.bid or {}).get("won_notes") or "")
        form.addRow("Won notes:", self.won_notes_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_confirm(self):
        if self.account_input.count() == 0:
            QMessageBox.warning(self, "Missing account", "No accounts linked to this bid.")
            return

        self.selected_customer_id = self.account_input.currentData()
        self.salesperson = self.salesperson_input.currentText().strip()
        self.project_manager = self.pm_input.currentText().strip()
        self.won_date = self.won_date_input.date().toString("yyyy-MM-dd")
        # Backward-compatible alias for older update paths.
        self.moraware_job_date = self.won_date
        self.won_notes = self.won_notes_input.toPlainText().strip()

        if self.est_complete_manual_input.isChecked():
            self.est_complete_date = self.est_complete_date_input.date().toString("yyyy-MM-dd")
            self.est_complete_date_manual = 1
        else:
            self.est_complete_date = None
            self.est_complete_date_manual = None

        if self.est_start_month_manual_input.isChecked():
            selected = self.est_start_month_input.date()
            self.est_start_month = QDate(selected.year(), selected.month(), 1).toString("yyyy-MM-dd")
        else:
            self.est_start_month = ""

        self.accept()


class AwardedTab(QWidget):
    SYNC_STALE_MINUTES = 60

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.main_window = parent
        self._selected_bid_id = None
        self._bids_cache = []
        self._build_ui()
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("PM Jobs")
        title.setObjectName("headingLabel")
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

        # --- Stats bar ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_total = StatCard("TOTAL AWARDED")
        self.stat_value = StatCard("TOTAL WON VALUE")
        self.stat_invoiced = StatCard("TOTAL INVOICED")
        self.stat_avg = StatCard("AVG JOB SIZE")
        for card in (self.stat_total, self.stat_value, self.stat_invoiced, self.stat_avg):
            stats_row.addWidget(card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # --- Filter bar ---
        filt = QHBoxLayout()
        filt.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search jobs...")
        self.search_input.setMaximumWidth(260)
        self.search_input.textChanged.connect(self._on_filter_changed)
        filt.addWidget(self.search_input)

        self.sp_combo = QComboBox()
        self.sp_combo.setMinimumWidth(140)
        self.sp_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.sp_combo)

        self.pm_combo = QComboBox()
        self.pm_combo.setMinimumWidth(140)
        self.pm_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.pm_combo)

        self.mw_sync_combo = QComboBox()
        self.mw_sync_combo.setMinimumWidth(120)
        self.mw_sync_combo.addItems(["All", "Synced", "Not Synced"])
        self.mw_sync_combo.setCurrentText("Synced")
        self.mw_sync_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.mw_sync_combo)

        self.mw_status_combo = QComboBox()
        self.mw_status_combo.setMinimumWidth(120)
        self.mw_status_combo.addItems(["All", "Active", "Complete"])
        self.mw_status_combo.setToolTip("Moraware job status for synced jobs only.")
        self.mw_status_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.mw_status_combo)

        self.job_type_combo = QComboBox()
        self.job_type_combo.setMinimumWidth(130)
        self.job_type_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.job_type_combo)

        self.stage_combo = QComboBox()
        self.stage_combo.setMinimumWidth(130)
        self.stage_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.stage_combo)

        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        filt.addWidget(clear_btn)

        filt.addStretch()

        self.showing_label = QLabel()
        self.showing_label.setObjectName("secondaryLabel")
        filt.addWidget(self.showing_label)

        self.sync_btn = QPushButton("Sync Invoices from Moraware")
        self.sync_btn.setObjectName("primaryButton")
        self.sync_btn.setToolTip("Red means the current filtered PM view needs Moraware sync.")
        self.sync_btn.clicked.connect(self._on_sync_all)
        filt.addWidget(self.sync_btn)

        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self._on_export_excel)
        filt.addWidget(self.export_btn)

        layout.addLayout(filt)
        helper = QLabel("Status filters apply to synced jobs. Red sync button means current filtered rows need refresh.")
        helper.setObjectName("secondaryLabel")
        layout.addWidget(helper)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "#", "Date Won", "Job Name", "Account", "Salesperson",
            "PM", "Job Type", "Bid Total", "Invoice Status", "Est Complete", "MW Job #"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.clicked.connect(self._on_row_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.setSortingEnabled(False)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(10, QHeaderView.ResizeToContents)

        layout.addWidget(self.table, 1)

        # --- Detail panel ---
        self.detail_panel = AwardedDetailPanel(self)
        self.detail_panel.action_triggered.connect(self._on_detail_action)
        layout.addWidget(self.detail_panel)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh(self):
        self._refresh_filter_combos()
        self._refresh_stats()
        self._load_bids()

    def _refresh_filter_combos(self):
        cur_sp = self.sp_combo.currentText()
        self.sp_combo.blockSignals(True)
        self.sp_combo.clear()
        self.sp_combo.addItem("All Salespersons")
        for s in self.db.get_salespersons():
            self.sp_combo.addItem(s)
        idx = self.sp_combo.findText(cur_sp)
        if idx >= 0:
            self.sp_combo.setCurrentIndex(idx)
        self.sp_combo.blockSignals(False)

        cur_pm = self.pm_combo.currentText()
        self.pm_combo.blockSignals(True)
        self.pm_combo.clear()
        self.pm_combo.addItem("All Project Managers")
        for p in self.db.get_project_managers():
            self.pm_combo.addItem(p)
        idx = self.pm_combo.findText(cur_pm)
        if idx >= 0:
            self.pm_combo.setCurrentIndex(idx)
        self.pm_combo.blockSignals(False)

        cur_job_type = self.job_type_combo.currentText()
        self.job_type_combo.blockSignals(True)
        self.job_type_combo.clear()
        self.job_type_combo.addItems([
            "All Job Types",
            "Solid Surface",
            "Stone",
            "Mixed",
            "Unassigned",
        ])
        idx = self.job_type_combo.findText(cur_job_type)
        if idx >= 0:
            self.job_type_combo.setCurrentIndex(idx)
        self.job_type_combo.blockSignals(False)

        cur_stage = self.stage_combo.currentText()
        self.stage_combo.blockSignals(True)
        self.stage_combo.clear()
        self.stage_combo.addItems([
            "All Stages",
            "Not Started",
            "In Progress",
            "Complete",
        ])
        idx = self.stage_combo.findText(cur_stage)
        if idx >= 0:
            self.stage_combo.setCurrentIndex(idx)
        self.stage_combo.blockSignals(False)

    def _refresh_stats(self):
        stats = self.db.get_awarded_stats()
        self.stat_total.set_value(stats["total_awarded"])
        self.stat_value.set_value(f"${stats['total_won_value']:,.0f}")
        self.stat_invoiced.set_value(f"${stats['total_invoiced']:,.0f}")
        self.stat_avg.set_value(f"${stats['avg_job_size']:,.0f}")

    def _get_filters(self):
        search = self.search_input.text().strip()
        sp = self.sp_combo.currentText()
        if sp == "All Salespersons":
            sp = ""
        pm = self.pm_combo.currentText()
        if pm == "All Project Managers":
            pm = ""
        mw_sync_state = self.mw_sync_combo.currentText()
        if mw_sync_state == "All":
            mw_sync_state = ""
        mw_status = self.mw_status_combo.currentText()
        if mw_status == "All":
            mw_status = ""
        job_type = self.job_type_combo.currentText()
        if job_type == "All Job Types":
            job_type = ""
        stage = self.stage_combo.currentText()
        if stage == "All Stages":
            stage = ""
        return search, sp, pm, mw_sync_state, mw_status, job_type, stage

    def _load_bids(self, scroll_to_bottom=True, select_bid_id=None):
        search, sp, pm, mw_sync_state, mw_status, job_type_filter, stage_filter = self._get_filters()
        bids = self.db.get_awarded_bids(
            search=search,
            salesperson=sp,
            project_manager=pm,
            moraware_status=mw_status,
            moraware_sync_state=mw_sync_state,
        )
        notebook_status_map = self.db.get_pm_notebook_status()
        job_type_map = self.db.get_pm_job_type()

        if job_type_filter:
            bids = [b for b in bids if job_type_map.get(b["id"], "Unassigned") == job_type_filter]
        if stage_filter:
            if stage_filter == "Not Started":
                bids = [b for b in bids if notebook_status_map.get(b["id"], "Pending") == "Pending"]
            elif stage_filter == "In Progress":
                bids = [
                    b for b in bids
                    if notebook_status_map.get(b["id"], "Pending") == "Active"
                    and (b.get("invoice_status_calc") or "Pending") != "Invoiced"
                ]
            elif stage_filter == "Complete":
                bids = [b for b in bids if (b.get("invoice_status_calc") or "Pending") == "Invoiced"]

        self._bids_cache = bids

        total_awarded = self.db.get_awarded_stats()["total_awarded"]
        self.showing_label.setText(f"Showing {len(bids)} of {total_awarded} PM jobs")

        self.table.setRowCount(len(bids))

        select_row = -1
        for row, b in enumerate(bids):
            bid_id = b["id"]
            if select_bid_id and bid_id == select_bid_id:
                select_row = row

            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setData(Qt.UserRole, bid_id)
            self.table.setItem(row, 0, num_item)

            won_date = b.get("won_date") or b.get("original_bid_date") or ""
            self.table.setItem(row, 1, QTableWidgetItem(self._fmt_date(won_date)))

            self.table.setItem(row, 2, QTableWidgetItem(b.get("bid_name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(b.get("won_customer_name") or ""))
            self.table.setItem(row, 4, QTableWidgetItem(b.get("salesperson") or ""))
            self.table.setItem(row, 5, QTableWidgetItem(b.get("project_manager") or ""))
            self.table.setItem(row, 6, QTableWidgetItem(job_type_map.get(bid_id, "Unassigned")))

            total_val = b.get("bid_total") or 0
            total_item = QTableWidgetItem(f"${total_val:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 7, total_item)

            # Invoice status badge
            inv_status = b.get("invoice_status_calc", "Pending")
            self.table.setItem(row, 8, QTableWidgetItem(inv_status))
            status_label = QLabel(inv_status)
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet(self._invoice_badge_style(inv_status))
            self.table.setCellWidget(row, 8, status_label)

            est_complete = self._fmt_date(b.get("est_complete_date") or "")
            self.table.setItem(row, 9, QTableWidgetItem(est_complete))

            mw_job_num = (b.get("moraware_job_number") or "").strip()
            self.table.setItem(row, 10, QTableWidgetItem(mw_job_num))

            notebook_status = notebook_status_map.get(bid_id, "Pending")
            if notebook_status == "Pending":
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#FFA07A"))

            self.table.setRowHeight(row, 40)

        if select_row >= 0:
            self.table.selectRow(select_row)
            self.table.scrollToItem(self.table.item(select_row, 0))
            self._show_detail(select_bid_id)
        elif scroll_to_bottom and self.table.rowCount() > 0:
            self.table.scrollToBottom()
        self._update_sync_button_state(bids)

    def _row_needs_sync(self, bid: dict) -> bool:
        has_link = bool((bid.get("moraware_job_id") or "").strip())
        if not has_link:
            return True

        job_status = (bid.get("moraware_job_status") or "").strip()
        if job_status not in ("Active", "Complete"):
            return True

        last_sync = (bid.get("last_moraware_sync_at") or "").strip()
        if not last_sync:
            return True

        parsed = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(last_sync, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return True
        return datetime.now() - parsed > timedelta(minutes=self.SYNC_STALE_MINUTES)

    def _update_sync_button_state(self, bids: list):
        needs_sync = any(self._row_needs_sync(b) for b in bids)
        if needs_sync:
            self.sync_btn.setStyleSheet(
                "background-color: #8b1f1f; color: #ffffff; border: 1px solid #a94442;"
            )
            self.sync_btn.setToolTip(
                "Current filtered rows are not fully synced (missing link/status or stale > 60 min)."
            )
        else:
            self.sync_btn.setStyleSheet("")
            self.sync_btn.setToolTip("Current filtered rows are up to date.")

    @staticmethod
    def _fmt_date(date_str):
        if not date_str:
            return ""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%m/%d/%Y")
        except (ValueError, TypeError):
            return date_str

    @staticmethod
    def _invoice_badge_style(status):
        if status == "Invoiced":
            return (
                "background-color: #1a3a1a; color: #4caf50; border-radius: 8px;"
                "padding: 3px 12px; font-size: 11px; font-weight: 600;"
            )
        elif status == "Partial":
            return (
                "background-color: #3a2a00; color: #ff9800; border-radius: 8px;"
                "padding: 3px 12px; font-size: 11px; font-weight: 600;"
            )
        else:
            return (
                "background-color: #2a2a2a; color: #666666; border-radius: 8px;"
                "padding: 3px 12px; font-size: 11px; font-weight: 600;"
            )

    # ------------------------------------------------------------------
    # Filter events
    # ------------------------------------------------------------------
    def _on_filter_changed(self):
        self._load_bids(scroll_to_bottom=True)

    def _clear_filters(self):
        self.search_input.clear()
        self.sp_combo.setCurrentIndex(0)
        self.pm_combo.setCurrentIndex(0)
        synced_idx = self.mw_sync_combo.findText("Synced")
        self.mw_sync_combo.setCurrentIndex(synced_idx if synced_idx >= 0 else 0)
        self.mw_status_combo.setCurrentIndex(0)
        self.job_type_combo.setCurrentIndex(0)
        self.stage_combo.setCurrentIndex(0)
        self._load_bids()

    # ------------------------------------------------------------------
    # Row interactions
    # ------------------------------------------------------------------
    def _get_bid_id_at_row(self, row):
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_row_clicked(self, index):
        bid_id = self._get_bid_id_at_row(index.row())
        if bid_id:
            self._show_detail(bid_id)

    def _show_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        row = idx.row()
        if row < 0:
            return

        bid_id = self._get_bid_id_at_row(row)
        if not bid_id:
            return

        self.table.selectRow(row)
        self._show_detail(bid_id)

        menu = QMenu(self)
        edit_job_action = menu.addAction("Edit Job")
        open_moraware_action = menu.addAction("Open in Moraware")
        move_back_action = menu.addAction("Move Back to Bidding")
        chosen = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if chosen == edit_job_action:
            self._edit_job(bid_id)
        elif chosen == open_moraware_action:
            self._open_in_moraware(bid_id)
        elif chosen == move_back_action:
            self._move_back_to_bidding(bid_id)

    def _show_detail(self, bid_id):
        self._selected_bid_id = bid_id
        self.detail_panel.load_bid(self.db, bid_id)

    # ------------------------------------------------------------------
    # Detail panel actions
    # ------------------------------------------------------------------
    def _on_detail_action(self, action, bid_id):
        if action == "edit_won":
            self._edit_job(bid_id)
        elif action == "refresh_invoices":
            self._refresh_single_job(bid_id)
        elif action == "move_back":
            self._move_back_to_bidding(bid_id)
        elif action == "open_bid_folder":
            self._open_bid_folder(bid_id)

    def _edit_job(self, bid_id):
        dlg = PMEditJobDialog(self.db, bid_id, self)
        if dlg.exec_() and dlg.selected_customer_id:
            self.db.update_won_details(
                bid_id, dlg.selected_customer_id,
                salesperson=dlg.salesperson,
                project_manager=dlg.project_manager,
                won_notes=dlg.won_notes,
                est_complete_date=dlg.est_complete_date,
                est_complete_date_manual=dlg.est_complete_date_manual,
                est_start_month=dlg.est_start_month,
                won_date=dlg.won_date,
            )
            self._refresh_stats()
            self._refresh_filter_combos()
            self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)

    def _open_in_moraware(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return

        moraware_job_id = (bid.get("moraware_job_id") or "").strip()
        if not moraware_job_id:
            QMessageBox.information(
                self,
                "No Moraware Link",
                "This job does not have a Moraware Job ID yet.",
            )
            return

        configured_url = (get_config().get("moraware_url") or "").strip()
        parsed = urlparse(configured_url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
        if not origin:
            QMessageBox.warning(
                self,
                "Moraware URL Missing",
                "Set your Moraware URL in Settings before opening jobs in Moraware.",
            )
            return

        webbrowser.open(f"{origin}/sys/job/{moraware_job_id}")

    def _on_export_excel(self):
        try:
            from PyQt5.QtWidgets import QFileDialog
            from utils.excel_export import export_pm_jobs

            path, _ = QFileDialog.getSaveFileName(
                self, "Export PM Jobs", "pm_jobs_export.xlsx", "Excel Files (*.xlsx)"
            )
            if not path:
                return

            notebook_status_map = self.db.get_pm_notebook_status()
            job_type_map = self.db.get_pm_job_type()
            rows = []
            for bid in self._bids_cache:
                bid_id = bid["id"]
                rows.append({
                    "date_won": bid.get("won_date") or bid.get("original_bid_date") or "",
                    "job_name": bid.get("bid_name") or "",
                    "account": bid.get("won_customer_name") or "",
                    "salesperson": bid.get("salesperson") or "",
                    "project_manager": bid.get("project_manager") or "",
                    "job_type": job_type_map.get(bid_id, "Unassigned"),
                    "bid_total": bid.get("bid_total") or 0,
                    "invoice_status": bid.get("invoice_status_calc", "Pending"),
                    "est_complete_date": bid.get("est_complete_date") or "",
                    "moraware_date": bid.get("moraware_created_date") or "",
                    "notebook_status": notebook_status_map.get(bid_id, "Pending"),
                })

            export_pm_jobs(rows, path)
            QMessageBox.information(self, "Export Complete", f"Exported {len(rows)} PM jobs to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _open_bid_folder(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return

        original_bid_date = bid.get("original_bid_date")
        if not original_bid_date:
            QMessageBox.warning(self, "Missing Bid Date", "This bid has no original bid date.")
            return

        try:
            bid_date = datetime.strptime(original_bid_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            QMessageBox.warning(
                self,
                "Invalid Bid Date",
                f"Could not parse original bid date: {original_bid_date}",
            )
            return

        cfg = get_config()
        dropbox_bids_path = (cfg.get("dropbox_bids_path") or "").strip()
        if not dropbox_bids_path:
            QMessageBox.warning(
                self,
                "Dropbox Path Not Configured",
                "Set the Dropbox bids root path in Settings first.",
            )
            return

        year_path = os.path.join(dropbox_bids_path, str(bid_date.year))
        if not os.path.isdir(year_path):
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Year folder not found:\n{year_path}",
            )
            return

        month_folder_map = {
            1: "1- January",
            2: "2 -February",
            3: "3 - March",
            4: "4 - April",
            5: "5 - May",
            6: "6 - June",
            7: "7 - July",
            8: "8 - August",
            9: "9 - September",
            10: "10 - October",
            11: "11 - November",
            12: "12- December",
        }
        exact_month_folder = month_folder_map[bid_date.month]
        month_path = os.path.join(year_path, exact_month_folder)

        if not os.path.isdir(month_path):
            month_name = bid_date.strftime("%B").lower()
            fallback_match = None
            for entry in os.listdir(year_path):
                candidate_path = os.path.join(year_path, entry)
                if not os.path.isdir(candidate_path):
                    continue
                normalized = entry.replace("-", " ").replace("_", " ").lower()
                if normalized.startswith(str(bid_date.month)) and month_name in normalized:
                    fallback_match = candidate_path
                    break
            if fallback_match:
                month_path = fallback_match

        if not os.path.isdir(month_path):
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Could not find month folder for {bid_date.strftime('%B %Y')}.\n"
                f"Expected:\n{month_path}",
            )
            return

        os.startfile(month_path)

    def _edit_won_details(self, bid_id):
        dlg = MarkWonDialog(self.db, bid_id, self, edit_mode=True)
        if dlg.exec_() and dlg.selected_customer_id:
            self.db.update_won_details(
                bid_id, dlg.selected_customer_id,
                salesperson=dlg.salesperson,
                project_manager=dlg.project_manager,
                won_notes=dlg.won_notes,
                won_date=dlg.won_date,
            )
            self._refresh_stats()
            self._refresh_filter_combos()
            self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)

    def _move_back_to_bidding(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return
        reply = QMessageBox.question(
            self, "Move Back to Bidding",
            f"Move '{bid['bid_name']}' back to PENDING status?\n\n"
            "This will clear all won details and invoice data.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.move_bid_back_to_bidding(bid_id)
            self.detail_panel.hide()
            self._selected_bid_id = None
            self._refresh_stats()
            self._load_bids()

    # ------------------------------------------------------------------
    # Moraware invoice sync
    # ------------------------------------------------------------------
    def _on_sync_all(self):
        cfg = get_config()
        if not all([cfg.get("moraware_username"), cfg.get("moraware_password"), cfg.get("moraware_url")]):
            QMessageBox.warning(
                self, "Moraware Not Configured",
                "Moraware credentials are not set.\n"
                "Go to Settings to configure your Moraware URL, username, and password."
            )
            return

        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("Syncing...")

        self._worker = InvoiceSyncWorker(self.db)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.start()

    def _refresh_single_job(self, bid_id):
        cfg = get_config()
        if not all([cfg.get("moraware_username"), cfg.get("moraware_password"), cfg.get("moraware_url")]):
            QMessageBox.warning(
                self, "Moraware Not Configured",
                "Moraware credentials are not set.\n"
                "Go to Settings to configure your Moraware URL, username, and password."
            )
            return

        bid = self.db.get_bid_by_id(bid_id)
        if not bid or not bid.get("moraware_job_id"):
            QMessageBox.information(
                self, "No Moraware Link",
                "This bid has no Moraware Job ID.\n"
                "Use the Moraware Sync dialog to link it first."
            )
            return

        self._worker = InvoiceSyncWorker(self.db, single_bid_id=bid_id)
        self._worker.finished.connect(lambda jobs, phases: self._on_single_sync_done(bid_id, phases))
        self._worker.error.connect(self._on_sync_error)
        self._worker.start()

    def _on_sync_finished(self, jobs_synced, phases_found):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("Sync Invoices from Moraware")
        self._refresh_stats()
        self._load_bids(scroll_to_bottom=False, select_bid_id=self._selected_bid_id)
        QMessageBox.information(
            self, "Sync Complete",
            f"{jobs_synced} jobs synced, {phases_found} invoice phases found."
        )

    def _on_single_sync_done(self, bid_id, phases_found):
        self._refresh_stats()
        self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)
        self.detail_panel.load_bid(self.db, bid_id)

    def _on_sync_error(self, error_msg):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("Sync Invoices from Moraware")
        QMessageBox.critical(self, "Sync Error", f"Invoice sync failed:\n{error_msg}")


class AwardedDetailPanel(QWidget):
    """Expandable detail panel for an awarded job, with invoice phase table."""
    action_triggered = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.bid_id = None
        self.setObjectName("detailPanel")
        self._build_ui()
        self.hide()

    def _build_ui(self):
        self.frame = QFrame()
        self.frame.setObjectName("detailPanel")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 8, 0, 0)
        outer.addWidget(self.frame)

        main_layout = QHBoxLayout(self.frame)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(24)

        # --- Left column: job info ---
        left = QVBoxLayout()
        left.setSpacing(8)

        self.lbl_name = QLabel()
        self.lbl_name.setObjectName("headingLabel")
        self.lbl_name.setWordWrap(True)
        left.addWidget(self.lbl_name)

        info_fields = [
            ("Original Bid Date", "lbl_bid_date"),
            ("Date Won", "lbl_won_date"),
            ("Moraware Date", "lbl_moraware_date"),
            ("Moraware Job #", "lbl_mw_job_number"),
            ("Winning Customer", "lbl_customer"),
            ("Salesperson", "lbl_salesperson"),
            ("Project Manager", "lbl_pm"),
            ("Bid Total", "lbl_bid_total"),
            ("Won Notes", "lbl_won_notes"),
        ]
        for label_text, attr in info_fields:
            row = QHBoxLayout()
            key = QLabel(f"{label_text}:")
            key.setObjectName("secondaryLabel")
            key.setFixedWidth(170)
            row.addWidget(key)
            val = QLabel()
            val.setWordWrap(True)
            setattr(self, attr, val)
            row.addWidget(val, 1)
            left.addLayout(row)

        left.addStretch()
        main_layout.addLayout(left, 4)

        # --- Right column: invoice info ---
        right = QVBoxLayout()
        right.setSpacing(8)

        inv_header = QHBoxLayout()
        inv_title = QLabel("Invoice Information")
        inv_title.setObjectName("subheadingLabel")
        inv_header.addWidget(inv_title)
        inv_header.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Sync invoice data for this job from Moraware")
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.clicked.connect(lambda: self._emit("refresh_invoices"))
        inv_header.addWidget(self.refresh_btn)
        right.addLayout(inv_header)

        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(8)
        self.inv_table.setHorizontalHeaderLabels([
            "Phase", "TP Code", "Sq Ft", "Template Date", "Install Date",
            "Contact Customer", "Invoice Date", "Status"
        ])
        self.inv_table.setAlternatingRowColors(True)
        self.inv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.inv_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inv_table.verticalHeader().setVisible(False)
        self.inv_table.setShowGrid(False)

        ih = self.inv_table.horizontalHeader()
        ih.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        ih.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        ih.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        ih.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        ih.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        ih.setSectionResizeMode(5, QHeaderView.Stretch)
        ih.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        ih.setSectionResizeMode(7, QHeaderView.Interactive)
        self.inv_table.setColumnWidth(7, 92)
        self.inv_table.setMinimumHeight(100)
        right.addWidget(self.inv_table)

        self.inv_empty_label = QLabel("No invoice data. Click Refresh to sync from Moraware.")
        self.inv_empty_label.setObjectName("secondaryLabel")
        self.inv_empty_label.setAlignment(Qt.AlignCenter)
        right.addWidget(self.inv_empty_label)

        self.lbl_total_invoiced = QLabel()
        self.lbl_total_invoiced.setObjectName("subheadingLabel")
        right.addWidget(self.lbl_total_invoiced)

        right.addStretch()
        main_layout.addLayout(right, 6)

        # --- Action buttons ---
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)
        btn_bar.addStretch()

        self.btn_edit_won = QPushButton("Edit Won Details")
        self.btn_edit_won.clicked.connect(lambda: self._emit("edit_won"))
        btn_bar.addWidget(self.btn_edit_won)

        self.btn_refresh_inv = QPushButton("Refresh Invoices")
        self.btn_refresh_inv.setObjectName("primaryButton")
        self.btn_refresh_inv.clicked.connect(lambda: self._emit("refresh_invoices"))
        btn_bar.addWidget(self.btn_refresh_inv)

        self.btn_move_back = QPushButton("Move Back to Bidding")
        self.btn_move_back.setObjectName("dangerButton")
        self.btn_move_back.clicked.connect(lambda: self._emit("move_back"))
        btn_bar.addWidget(self.btn_move_back)

        self.btn_open_folder = QPushButton("Open Bid Folder")
        self.btn_open_folder.clicked.connect(lambda: self._emit("open_bid_folder"))
        btn_bar.addWidget(self.btn_open_folder)

        outer.addLayout(btn_bar)

    def _emit(self, action):
        if self.bid_id is not None:
            self.action_triggered.emit(action, self.bid_id)

    def load_bid(self, db, bid_id):
        self.db = db
        self.bid_id = bid_id
        bid = db.get_bid_by_id(bid_id)
        if not bid:
            self.hide()
            return

        self.lbl_name.setText(bid["bid_name"])

        self.lbl_bid_date.setText(self._fmt(bid.get("original_bid_date")))
        self.lbl_won_date.setText(self._fmt(bid.get("won_date")))
        self.lbl_moraware_date.setText(self._fmt(bid.get("moraware_created_date")))
        self.lbl_mw_job_number.setText((bid.get("moraware_job_number") or "").strip() or "\u2014")

        if bid.get("won_customer_id"):
            customers = db.get_bid_customers(bid_id)
            wc = [c for c in customers if c["id"] == bid["won_customer_id"]]
            self.lbl_customer.setText(wc[0]["name"] if wc else "\u2014")
        else:
            self.lbl_customer.setText("\u2014")

        self.lbl_salesperson.setText(bid.get("salesperson") or "\u2014")
        self.lbl_pm.setText(bid.get("project_manager") or "\u2014")

        latest = db.get_latest_revision(bid_id)
        bid_total = latest["bid_total"] if latest else 0
        self.lbl_bid_total.setText(f"${bid_total:,.2f}")

        self.lbl_won_notes.setText(bid.get("won_notes") or "\u2014")

        # Invoice data
        invoices = db.get_invoice_data_for_bid(bid_id)
        if invoices:
            self.inv_table.show()
            self.inv_empty_label.hide()
            self.inv_table.setRowCount(len(invoices))
            total_tp = 0
            for row, inv in enumerate(invoices):
                self.inv_table.setItem(row, 0, QTableWidgetItem(inv.get("phase") or ""))

                tp = inv.get("tp_code") or 0
                total_tp += tp
                tp_item = QTableWidgetItem(f"${tp:,.2f}")
                tp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.inv_table.setItem(row, 1, tp_item)

                sq_ft = inv.get("sq_ft")
                sq_ft_text = f"{sq_ft:,.2f}" if isinstance(sq_ft, (int, float)) else "\u2014"
                sq_item = QTableWidgetItem(sq_ft_text)
                sq_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.inv_table.setItem(row, 2, sq_item)

                self.inv_table.setItem(
                    row, 3, QTableWidgetItem(self._fmt(inv.get("template_date")) if inv.get("template_date") else "\u2014")
                )
                self.inv_table.setItem(
                    row, 4, QTableWidgetItem(self._fmt(inv.get("install_date")) if inv.get("install_date") else "\u2014")
                )

                contact_date = self._fmt(inv.get("contact_customer_date")) if inv.get("contact_customer_date") else ""
                contact_notes = (inv.get("contact_customer_notes") or "").strip()
                if contact_date and contact_notes:
                    contact_text = f"{contact_date} - {contact_notes}"
                elif contact_date:
                    contact_text = contact_date
                elif contact_notes:
                    contact_text = contact_notes
                else:
                    contact_text = "\u2014"
                self.inv_table.setItem(row, 5, QTableWidgetItem(contact_text))

                inv_date = inv.get("invoice_date") or "\u2014"
                self.inv_table.setItem(
                    row, 6, QTableWidgetItem(self._fmt(inv_date) if inv_date != "\u2014" else "\u2014")
                )

                status = inv.get("invoice_status") or "Pending"
                status_label = QLabel(status)
                status_label.setAlignment(Qt.AlignCenter)
                status_label.setMinimumWidth(72)
                if status == "Complete":
                    status_label.setStyleSheet(
                        "background-color: #1a3a1a; color: #4caf50; border-radius: 6px;"
                        "padding: 2px 8px; font-size: 11px; font-weight: 600;"
                    )
                else:
                    status_label.setStyleSheet(
                        "background-color: #3a2a00; color: #ff9800; border-radius: 6px;"
                        "padding: 2px 8px; font-size: 11px; font-weight: 600;"
                    )
                self.inv_table.setCellWidget(row, 7, status_label)
                self.inv_table.setRowHeight(row, 36)

            self.lbl_total_invoiced.setText(f"Total Invoiced: ${total_tp:,.2f}")
        else:
            self.inv_table.hide()
            self.inv_table.setRowCount(0)
            self.inv_empty_label.show()
            self.lbl_total_invoiced.setText("")

        self.show()

    @staticmethod
    def _fmt(date_str):
        if not date_str:
            return "\u2014"
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%m/%d/%Y")
        except (ValueError, TypeError):
            return date_str
