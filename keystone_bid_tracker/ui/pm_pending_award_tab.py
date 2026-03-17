"""
Keystone Bid Tracker - PM Pending Award Tab
WON bids that are not linked to Moraware yet.
"""

import os
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QMessageBox,
)

from config import get_config
from ui.awarded_tab import PMEditJobDialog


class PMPendingAwardTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._rows_cache = []
        self._build_ui()
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("Pending Award")
        title.setObjectName("headingLabel")
        root.addWidget(title)
        sub = QLabel("WON bids not yet linked to a Moraware job")
        sub.setObjectName("secondaryLabel")
        root.addWidget(sub)

        filt = QHBoxLayout()
        filt.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search pending awards...")
        self.search_input.setMaximumWidth(280)
        self.search_input.textChanged.connect(self._load_rows)
        filt.addWidget(self.search_input)

        self.pm_combo = QComboBox()
        self.pm_combo.setMinimumWidth(180)
        self.pm_combo.currentIndexChanged.connect(self._load_rows)
        filt.addWidget(self.pm_combo)

        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        filt.addWidget(clear_btn)

        filt.addStretch()
        self.showing_label = QLabel("")
        self.showing_label.setObjectName("secondaryLabel")
        filt.addWidget(self.showing_label)
        root.addLayout(filt)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["#", "Date Won", "Job Name", "Account", "Salesperson", "PM", "Bid Total"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

    def refresh(self):
        self._refresh_pm_filter()
        self._load_rows()

    def _refresh_pm_filter(self):
        current = self.pm_combo.currentText()
        self.pm_combo.blockSignals(True)
        self.pm_combo.clear()
        self.pm_combo.addItem("All Project Managers")
        for pm in self.db.get_project_managers():
            self.pm_combo.addItem(pm)
        idx = self.pm_combo.findText(current)
        self.pm_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.pm_combo.blockSignals(False)

    def _load_rows(self):
        search = self.search_input.text().strip()
        pm = self.pm_combo.currentText().strip()
        if pm == "All Project Managers":
            pm = ""
        rows = self.db.get_pending_award_bids(search=search, project_manager=pm)
        self._rows_cache = rows

        self.table.setRowCount(len(rows))
        for row, bid in enumerate(rows):
            bid_id = bid["id"]
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setData(Qt.UserRole, bid_id)
            self.table.setItem(row, 0, num_item)

            won_date = bid.get("won_date") or bid.get("original_bid_date") or ""
            self.table.setItem(row, 1, QTableWidgetItem(self._fmt_date(won_date)))
            self.table.setItem(row, 2, QTableWidgetItem(bid.get("bid_name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(bid.get("won_customer_name") or ""))
            self.table.setItem(row, 4, QTableWidgetItem(bid.get("salesperson") or ""))
            self.table.setItem(row, 5, QTableWidgetItem(bid.get("project_manager") or ""))

            total = float(bid.get("bid_total") or 0)
            total_item = QTableWidgetItem(f"${total:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 6, total_item)
            self.table.setRowHeight(row, 38)

        self.showing_label.setText(f"Showing {len(rows)} pending awards")

    def _clear_filters(self):
        self.search_input.clear()
        self.pm_combo.setCurrentIndex(0)
        self._load_rows()

    def _show_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        if idx.row() < 0:
            return
        bid_id = self._get_bid_id_at_row(idx.row())
        if not bid_id:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit Job")
        move_back_action = menu.addAction("Move Back to Bidding")
        open_folder_action = menu.addAction("Open Bid Folder")

        chosen = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if chosen == edit_action:
            self._edit_job(bid_id)
        elif chosen == move_back_action:
            self._move_back_to_bidding(bid_id)
        elif chosen == open_folder_action:
            self._open_bid_folder(bid_id)

    def _get_bid_id_at_row(self, row):
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _edit_job(self, bid_id):
        dlg = PMEditJobDialog(self.db, bid_id, self)
        if dlg.exec_() and dlg.selected_customer_id:
            self.db.update_won_details(
                bid_id,
                dlg.selected_customer_id,
                salesperson=dlg.salesperson,
                project_manager=dlg.project_manager,
                won_notes=dlg.won_notes,
                est_complete_date=dlg.est_complete_date,
                est_complete_date_manual=dlg.est_complete_date_manual,
                est_start_month=dlg.est_start_month,
                won_date=dlg.won_date,
            )
            self.refresh()

    def _move_back_to_bidding(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return
        reply = QMessageBox.question(
            self,
            "Move Back to Bidding",
            f"Move '{bid['bid_name']}' back to PENDING status?\n\n"
            "This will clear all won details and invoice data.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.move_bid_back_to_bidding(bid_id)
            self.refresh()

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
                self, "Invalid Bid Date", f"Could not parse original bid date: {original_bid_date}"
            )
            return

        cfg = get_config()
        dropbox_bids_path = (cfg.get("dropbox_bids_path") or "").strip()
        if not dropbox_bids_path:
            QMessageBox.warning(
                self, "Dropbox Path Not Configured", "Set the Dropbox bids root path in Settings first."
            )
            return

        year_path = os.path.join(dropbox_bids_path, str(bid_date.year))
        if not os.path.isdir(year_path):
            QMessageBox.warning(self, "Folder Not Found", f"Year folder not found:\n{year_path}")
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
        month_path = os.path.join(year_path, month_folder_map[bid_date.month])
        if not os.path.isdir(month_path):
            month_name = bid_date.strftime("%B").lower()
            fallback = None
            for entry in os.listdir(year_path):
                candidate = os.path.join(year_path, entry)
                if not os.path.isdir(candidate):
                    continue
                normalized = entry.replace("-", " ").replace("_", " ").lower()
                if normalized.startswith(str(bid_date.month)) and month_name in normalized:
                    fallback = candidate
                    break
            if fallback:
                month_path = fallback

        if not os.path.isdir(month_path):
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Could not find month folder for {bid_date.strftime('%B %Y')}.\nExpected:\n{month_path}",
            )
            return
        os.startfile(month_path)

    @staticmethod
    def _fmt_date(date_str):
        if not date_str:
            return ""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
        except (ValueError, TypeError):
            return date_str
