"""
Keystone Bid Tracker - Link Local Bid Dialog
Select a local bid to link from PM Active Jobs.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
)


class LinkLocalBidDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_bid = None
        self._all_rows = []
        self._visible_rows = []
        self._build_ui()
        self._load_rows()

    def _build_ui(self):
        self.setWindowTitle("Link to Local Bid")
        self.setMinimumSize(900, 520)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search bids or accounts...")
        self.search_input.textChanged.connect(self._apply_filters)
        top.addWidget(self.search_input, 1)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses")
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        top.addWidget(self.status_combo)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_filters)
        top.addWidget(clear_btn)

        root.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["#", "Bid Name", "Status", "Account(s)", "Bid Date", "Bid Total"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(lambda _idx: self._accept_selection())

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        root.addWidget(self.status_label)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        link_btn = QPushButton("Link Selected Bid")
        link_btn.setObjectName("primaryButton")
        link_btn.clicked.connect(self._accept_selection)
        btns.addWidget(link_btn)
        root.addLayout(btns)

    def _load_rows(self):
        self._all_rows = self.db.get_linkable_bids(search="")
        statuses = sorted({(r.get("status") or "").strip() for r in self._all_rows if (r.get("status") or "").strip()})
        current = self.status_combo.currentText()
        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        self.status_combo.addItem("All Statuses")
        for s in statuses:
            self.status_combo.addItem(s)
        idx = self.status_combo.findText(current)
        self.status_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.status_combo.blockSignals(False)
        self._apply_filters()

    def _apply_filters(self):
        q = (self.search_input.text() or "").strip().lower()
        chosen_status = (self.status_combo.currentText() or "").strip()
        rows = list(self._all_rows)
        if chosen_status and chosen_status != "All Statuses":
            rows = [r for r in rows if (r.get("status") or "").strip() == chosen_status]
        if q:
            rows = [
                r for r in rows
                if q in (r.get("bid_name") or "").lower()
                or q in (r.get("customer_names") or "").lower()
                or q in str(r.get("id") or "").lower()
            ]
        self._visible_rows = rows
        self._render_rows()

    def _render_rows(self):
        rows = self._visible_rows
        self.table.setRowCount(len(rows))
        for i, bid in enumerate(rows):
            idx_item = QTableWidgetItem(str(i + 1))
            idx_item.setTextAlignment(Qt.AlignCenter)
            idx_item.setData(Qt.UserRole, bid.get("id"))
            self.table.setItem(i, 0, idx_item)
            self.table.setItem(i, 1, QTableWidgetItem(bid.get("bid_name") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(bid.get("status") or ""))
            self.table.setItem(i, 3, QTableWidgetItem(bid.get("customer_names") or ""))
            self.table.setItem(i, 4, QTableWidgetItem(bid.get("original_bid_date") or ""))
            total_item = QTableWidgetItem(f"${float(bid.get('bid_total') or 0):,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 5, total_item)
            self.table.setRowHeight(i, 36)
        self.status_label.setText(f"Showing {len(rows)} bids")

    def _clear_filters(self):
        self.search_input.clear()
        self.status_combo.setCurrentIndex(0)
        self._apply_filters()

    def _accept_selection(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._visible_rows):
            return
        self.selected_bid = self._visible_rows[row]
        self.accept()
