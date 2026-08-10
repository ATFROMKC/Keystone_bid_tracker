"""
Keystone Bid Tracker - Bids Tab (Main View)
Stats bar, filter bar, bid table, expandable detail panel, context menu.
"""

import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QHeaderView, QMenu,
    QAction, QMessageBox, QFrame, QAbstractItemView, QSplitter,
    QScrollArea, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor

from config import get_config
from styles.theme import get_status_style, COLORS
from ui.bid_detail import BidDetailPanel
from ui.add_bid_dialog import AddBidDialog
from ui.add_revision_dialog import AddRevisionDialog
from ui.mark_won_dialog import MarkWonDialog
from ui.moraware_sync_dialog import MorewareSyncDialog
from ui.manual_sync_dialog import ManualSyncDialog


class StatCard(QFrame):
    """Small card widget for the summary stats bar."""
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


class BidsTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._selected_bid_id = None
        self._mw_job_cache = []  # persists across ManualSyncDialog sessions
        self._build_ui()
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # --- Top section: left (title+stats) | center (logo) | right (buttons) ---
        top_section = QHBoxLayout()
        top_section.setSpacing(16)

        # Left column: heading + stats
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        title = QLabel("Bids")
        title.setObjectName("headingLabel")
        left_col.addWidget(title)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_total = StatCard("TOTAL BIDS")
        self.stat_value = StatCard("TOTAL VALUE")
        self.stat_won = StatCard("WON")
        self.stat_won_value = StatCard("TOTAL WON VALUE")
        self.stat_win_pct = StatCard("WIN %")
        self._stat_cards = [
            self.stat_total,
            self.stat_value,
            self.stat_won,
            self.stat_won_value,
            self.stat_win_pct,
        ]
        for card in self._stat_cards:
            stats_row.addWidget(card)
        left_col.addLayout(stats_row)
        top_section.addLayout(left_col, 7)
        self._stats_row_layout = stats_row

        # Center: logo + subtitle
        logo_col = QVBoxLayout()
        logo_col.setSpacing(2)
        logo_col.addStretch()

        self._logo_label = QLabel()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Assets", "Keystone-Logo-600-DPI.png",
        )
        self._logo_pixmap = QPixmap(logo_path)
        if not self._logo_pixmap.isNull():
            scaled = self._logo_pixmap.scaledToHeight(92, Qt.SmoothTransformation)
            self._logo_label.setPixmap(scaled)
        self._logo_label.setAlignment(Qt.AlignCenter)
        self._logo_label.setMinimumWidth(200)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        glow.setColor(QColor(74, 158, 255, 153))
        self._logo_label.setGraphicsEffect(glow)
        logo_col.addWidget(self._logo_label)

        subtitle = QLabel("BID TRACKER")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 9px; font-weight: bold; letter-spacing: 3px;"
            "color: #4a9eff; padding: 0; margin: 0;"
        )
        logo_col.addWidget(subtitle)
        logo_col.addStretch()
        top_section.addLayout(logo_col, 3)

        # Right column: buttons (top-aligned)
        right_col = QVBoxLayout()
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.export_btn = QPushButton("Export All")
        self.export_btn.clicked.connect(self._on_export_all)
        btn_row.addWidget(self.export_btn)

        self.sync_btn = QPushButton("Moraware Sync")
        self.sync_btn.clicked.connect(self._on_open_sync_dialog)
        btn_row.addWidget(self.sync_btn)

        self.add_btn = QPushButton("+ Add Bid")
        self.add_btn.setObjectName("addBidButton")
        self.add_btn.clicked.connect(self._on_add_bid)
        btn_row.addWidget(self.add_btn)

        right_col.addLayout(btn_row)
        right_col.addStretch()
        top_section.addLayout(right_col, 2)

        layout.addLayout(top_section)

        # --- Filter bar ---
        filt = QHBoxLayout()
        filt.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search bids...")
        self.search_input.setMaximumWidth(260)
        self.search_input.textChanged.connect(self._on_filter_changed)
        filt.addWidget(self.search_input)

        self.estimator_combo = QComboBox()
        self.estimator_combo.setMinimumWidth(140)
        self.estimator_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.estimator_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Status", "PENDING", "BIDDING", "WON"])
        self.status_combo.setMinimumWidth(120)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.status_combo)

        self.year_combo = QComboBox()
        self.year_combo.setMinimumWidth(100)
        self.year_combo.currentIndexChanged.connect(self._on_filter_changed)
        filt.addWidget(self.year_combo)

        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        filt.addWidget(clear_btn)

        filt.addStretch()

        self.showing_label = QLabel()
        self.showing_label.setObjectName("secondaryLabel")
        filt.addWidget(self.showing_label)
        layout.addLayout(filt)

        # --- Bid table ---
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "#", "Date", "Estimator", "Bid Name", "Accounts",
            "Bid Total", "Stone SF", "Solid SF", "Status", "Rev", "MW"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.clicked.connect(self._on_row_clicked)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        self.table.setSortingEnabled(False)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # #
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Date
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Estimator
        h.setSectionResizeMode(3, QHeaderView.Stretch)           # Bid Name
        h.setSectionResizeMode(4, QHeaderView.Stretch)           # Customers
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Bid Total
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Stone SF
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Solid SF
        h.setSectionResizeMode(8, QHeaderView.Fixed)              # Status
        h.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Rev
        h.setSectionResizeMode(10, QHeaderView.ResizeToContents) # MW
        self.table.setColumnWidth(8, 100)

        layout.addWidget(self.table, 1)

        # --- Detail panel ---
        self.detail_panel = BidDetailPanel(self)
        self.detail_panel.action_triggered.connect(self._on_detail_action)
        self.detail_panel.close_requested.connect(self._on_hide_detail)
        layout.addWidget(self.detail_panel)
        self._apply_responsive_header(self.width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_header(event.size().width())

    def _apply_responsive_header(self, width):
        if self._logo_pixmap.isNull():
            return

        if width < 1450:
            card_min_width = 130
            stats_spacing = 8
            logo_height = 62
        elif width < 1750:
            card_min_width = 145
            stats_spacing = 10
            logo_height = 82
        elif width < 2100:
            card_min_width = 160
            stats_spacing = 12
            logo_height = 102
        else:
            card_min_width = 170
            stats_spacing = 12
            logo_height = 118

        self._stats_row_layout.setSpacing(stats_spacing)
        for card in self._stat_cards:
            card.setMinimumWidth(card_min_width)

        target_h = max(50, logo_height)
        current = self._logo_label.pixmap()
        if current and abs(current.height() - target_h) < 4:
            return
        scaled = self._logo_pixmap.scaledToHeight(target_h, Qt.SmoothTransformation)
        self._logo_label.setPixmap(scaled)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh(self):
        self._refresh_filter_combos()
        self._load_bids()

    def _refresh_filter_combos(self):
        # Estimator combo
        current_est = self.estimator_combo.currentText()
        self.estimator_combo.blockSignals(True)
        self.estimator_combo.clear()
        self.estimator_combo.addItem("All Estimators")
        for e in self.db.get_estimators():
            self.estimator_combo.addItem(e)
        idx = self.estimator_combo.findText(current_est)
        if idx >= 0:
            self.estimator_combo.setCurrentIndex(idx)
        self.estimator_combo.blockSignals(False)

        # Year combo
        current_yr = self.year_combo.currentText()
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        self.year_combo.addItem("All Years")
        for y in self.db.get_years():
            self.year_combo.addItem(y)
        idx = self.year_combo.findText(current_yr)
        if idx >= 0:
            self.year_combo.setCurrentIndex(idx)
        self.year_combo.blockSignals(False)

    def _refresh_stats(self, bids):
        total = len(bids)
        won = sum(1 for b in bids if (b.get("status") or "").upper() == "WON")
        total_value = sum(float(b.get("bid_total") or 0) for b in bids)
        total_won_value = sum(
            float(b.get("bid_total") or 0)
            for b in bids
            if (b.get("status") or "").upper() == "WON"
        )
        win_pct = (won / total * 100.0) if total > 0 else 0.0
        self.stat_total.set_value(total)
        self.stat_value.set_value(f"${total_value:,.0f}")
        self.stat_won.set_value(won)
        self.stat_won_value.set_value(f"${total_won_value:,.0f}")
        self.stat_win_pct.set_value(f"{win_pct:.1f}%")

    def _get_filters(self):
        search = self.search_input.text().strip()
        est = self.estimator_combo.currentText()
        if est == "All Estimators":
            est = ""
        status = self.status_combo.currentText()
        if status == "All Status":
            status = ""
        year = self.year_combo.currentText()
        if year == "All Years":
            year = ""
        return search, est, status, year

    def _load_bids(self, scroll_to_bottom=True, select_bid_id=None):
        search, est, status, year = self._get_filters()
        bids = self.db.get_bids(search=search, estimator=est, status=status, year=year)
        self._refresh_stats(bids)

        self.showing_label.setText(f"Showing {len(bids)} bids")

        self.table.setRowCount(len(bids))

        select_row = -1
        for row, b in enumerate(bids):
            bid_id = b["id"]
            if select_bid_id and bid_id == select_bid_id:
                select_row = row

            # # column
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setData(Qt.UserRole, bid_id)
            self.table.setItem(row, 0, num_item)

            # Date
            try:
                d = datetime.strptime(b["original_bid_date"], "%Y-%m-%d")
                date_str = d.strftime("%m/%d/%Y")
            except (ValueError, TypeError):
                date_str = b["original_bid_date"] or ""
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Estimator
            self.table.setItem(row, 2, QTableWidgetItem(b["estimator"] or ""))

            # Bid Name
            self.table.setItem(row, 3, QTableWidgetItem(b["bid_name"] or ""))

            # Customers
            self.table.setItem(row, 4, QTableWidgetItem(b["customer_names"] or ""))

            # Bid Total
            total_val = b["bid_total"] or 0
            total_item = QTableWidgetItem(f"${total_val:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, total_item)

            # Stone SF
            stone_val = b["stone_sf"] or 0
            stone_item = QTableWidgetItem(f"{stone_val:,.0f}")
            stone_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 6, stone_item)

            # Solid SF
            solid_val = b["solid_surf_sf"] or 0
            solid_item = QTableWidgetItem(f"{solid_val:,.0f}")
            solid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 7, solid_item)

            # Status pill
            status_label = QLabel(b["status"])
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet(get_status_style(b["status"]))
            self.table.setCellWidget(row, 8, status_label)

            # Rev
            rev_item = QTableWidgetItem(str(b["revision_no"] or 1))
            rev_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 9, rev_item)

            # MW rule: only WON bids show an unsynced indicator.
            mw_synced = bool((b.get("moraware_job_id") or "").strip())
            is_won = (b.get("status") or "").upper() == "WON"
            mw_symbol = "✓" if mw_synced else ("⊘" if is_won else "")
            mw_item = QTableWidgetItem(mw_symbol)
            mw_item.setTextAlignment(Qt.AlignCenter)
            if mw_synced:
                mw_item.setForeground(QColor("#4caf50"))
            elif is_won:
                mw_item.setForeground(QColor("#d9534f"))
            self.table.setItem(row, 10, mw_item)

            self.table.setRowHeight(row, 40)

        if select_row >= 0:
            self.table.selectRow(select_row)
            self.table.scrollToItem(self.table.item(select_row, 0))
            self._show_detail(select_bid_id)
        elif scroll_to_bottom and self.table.rowCount() > 0:
            self.table.scrollToBottom()

    # ------------------------------------------------------------------
    # Filter events
    # ------------------------------------------------------------------
    def _on_filter_changed(self):
        self._load_bids(scroll_to_bottom=True)

    def _clear_filters(self):
        self.search_input.clear()
        self.estimator_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.year_combo.setCurrentIndex(0)
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

    def _on_row_double_clicked(self, index):
        bid_id = self._get_bid_id_at_row(index.row())
        if bid_id:
            self._edit_bid(bid_id)

    def _show_detail(self, bid_id):
        self._selected_bid_id = bid_id
        self.detail_panel.load_bid(self.db, bid_id)

    def open_bid(self, bid_id):
        """Select and show a bid (used from Bid Board linked bids)."""
        self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)
        try:
            self._show_detail(bid_id)
        except Exception:
            QMessageBox.warning(self, "Bid not found", f"Could not open bid #{bid_id}.")

    def _on_hide_detail(self):
        self.detail_panel.hide()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------
    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        bid_id = self._get_bid_id_at_row(row)
        if not bid_id:
            return

        bid = self.db.get_bid_by_id(bid_id)
        menu = QMenu(self)

        edit_action = menu.addAction("Edit")
        rev_action = menu.addAction("Add Revision")
        menu.addSeparator()
        won_action = menu.addAction("Mark Won")
        menu.addSeparator()
        export_action = menu.addAction("Export to Excel")
        open_folder_action = menu.addAction("Open Bid Folder")
        menu.addSeparator()
        sync_action = menu.addAction("\U0001f517 Sync with Moraware Job(s)")
        unsync_action = menu.addAction("🔗 Unsync from Moraware")
        unsync_action.setEnabled(bool(bid.get("moraware_job_id")))
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        if bid and bid["status"] == "WON":
            delete_action.setEnabled(False)

        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._edit_bid(bid_id)
        elif action == rev_action:
            self._add_revision(bid_id)
        elif action == won_action:
            self._mark_won(bid_id)
        elif action == export_action:
            self._export_single(bid_id)
        elif action == open_folder_action:
            self._open_bid_folder(bid_id)
        elif action == sync_action:
            self._manual_sync(bid_id)
        elif action == unsync_action:
            confirm = QMessageBox.question(
                self, "Unsync from Moraware",
                f"Unsync '{bid['bid_name']}' from Moraware?\n\n"
                "This removes Moraware links and synced invoice rows, but keeps bid status unchanged.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                self.db.unsync_bid_from_moraware(bid["id"])
                self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)
        elif action == delete_action:
            self._delete_bid(bid_id)

    def _manual_sync(self, bid_id):
        all_bids = self.db.get_bids()
        bid = next((b for b in all_bids if b["id"] == bid_id), None)
        if not bid:
            return
        dlg = ManualSyncDialog(bid, self.db, job_cache=self._mw_job_cache, parent=self)
        if dlg.exec_() == ManualSyncDialog.Accepted:
            self._load_bids()

    # ------------------------------------------------------------------
    # Detail panel actions
    # ------------------------------------------------------------------
    def _on_detail_action(self, action, bid_id):
        if action == "add_revision":
            self._add_revision(bid_id)
        elif action == "mark_won":
            self._mark_won(bid_id)
        elif action == "edit":
            self._edit_bid(bid_id)
        elif action == "delete":
            self._delete_bid(bid_id)
        elif action == "link_mw":
            self._manual_sync(bid_id)
        elif action == "unlink_mw":
            bid = self.db.get_bid_by_id(bid_id)
            if not bid:
                return
            confirm = QMessageBox.question(
                self, "Unsync from Moraware",
                f"Unsync '{bid['bid_name']}' from Moraware?\n\n"
                "This removes Moraware links and synced invoice rows, but keeps bid status unchanged.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                self.db.unsync_bid_from_moraware(bid_id)
                self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)
        elif action == "open_bid_folder":
            self._open_bid_folder(bid_id)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
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

    def _on_add_bid(self):
        dlg = AddBidDialog(self.db, self)
        if dlg.exec_() and dlg.result_data:
            d = dlg.result_data
            bid_id = self.db.add_bid(
                d["bid_name"], d["estimator"], d["original_bid_date"],
                d["notes"], d["customer_ids"], d["bid_total"],
                d["solid_surf_sf"], d["stone_sf"],
                due_date=d.get("due_date"), location=d.get("location"),
            )
            self._refresh_filter_combos()
            self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)

    def _edit_bid(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return
        dlg = AddBidDialog(self.db, self, bid_data=bid)
        if dlg.exec_() and dlg.result_data:
            d = dlg.result_data
            self.db.update_bid(
                bid_id, d["bid_name"], d["estimator"],
                d["original_bid_date"], d["notes"], d["customer_ids"],
                due_date=d.get("due_date"), location=d.get("location"),
            )
            # Update revision 1 totals if this is the only revision
            latest = self.db.get_latest_revision(bid_id)
            if latest and latest["revision_no"] == 1:
                self.db.update_revision(
                    latest["id"], d["original_bid_date"],
                    d["bid_total"], d["solid_surf_sf"], d["stone_sf"],
                )
            new_status = d.get("status", bid["status"])
            if new_status != bid["status"]:
                self.db.mark_bid_status(bid_id, new_status)
            self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)

    def _add_revision(self, bid_id):
        dlg = AddRevisionDialog(self.db, bid_id, self)
        if dlg.exec_() and dlg.result_data:
            d = dlg.result_data
            self.db.add_revision(
                bid_id, d["revision_date"], d["bid_total"],
                d["solid_surf_sf"], d["stone_sf"], d["reason"],
            )
            self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)

    def _mark_won(self, bid_id):
        dlg = MarkWonDialog(self.db, bid_id, self)
        if dlg.exec_() and dlg.selected_customer_id:
            self.db.mark_bid_won(
                bid_id, dlg.selected_customer_id,
                salesperson=dlg.salesperson,
                project_manager=dlg.project_manager,
                won_notes=dlg.won_notes,
                won_date=dlg.won_date,
            )
            self._load_bids(scroll_to_bottom=False, select_bid_id=bid_id)

    def _delete_bid(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return
        if bid["status"] == "WON":
            QMessageBox.warning(self, "Cannot Delete", "WON bids cannot be deleted.")
            return
        reply = QMessageBox.question(
            self, "Delete Bid",
            f"Delete '{bid['bid_name']}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_bid(bid_id)
            self.detail_panel.hide()
            self._selected_bid_id = None
            self._load_bids()

    def _on_open_sync_dialog(self):
        dlg = MorewareSyncDialog(self.db, self)
        dlg.exec_()
        self.refresh()

    def _on_export_all(self):
        try:
            from utils.excel_export import export_bids
            from PyQt5.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Bids", "bid_export.xlsx",
                "Excel Files (*.xlsx)",
            )
            if path:
                bids = self.db.get_all_bids_for_export()
                export_bids(bids, path)
                QMessageBox.information(self, "Export Complete", f"Exported {len(bids)} bids to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _export_single(self, bid_id):
        try:
            from utils.excel_export import export_bids
            from PyQt5.QtWidgets import QFileDialog
            bid = self.db.get_bid_by_id(bid_id)
            default_name = f"{bid['bid_name']}.xlsx" if bid else "bid.xlsx"
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Bid", default_name,
                "Excel Files (*.xlsx)",
            )
            if path:
                bids = [b for b in self.db.get_all_bids_for_export() if b["id"] == bid_id]
                export_bids(bids, path)
                QMessageBox.information(self, "Export Complete", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
