"""
Keystone Bid Tracker - Bid Detail Panel
Expandable panel showing bid info (left) and revision history (right).
Emits signals for actions so the parent BidsTab can react.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QFrame, QAbstractItemView, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from styles.theme import get_status_style


class BidDetailPanel(QWidget):
    action_triggered = pyqtSignal(str, int)  # action_name, bid_id
    close_requested = pyqtSignal()

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

        # --- Left column: bid info ---
        left = QVBoxLayout()
        left.setSpacing(10)

        self.lbl_name = QLabel()
        self.lbl_name.setObjectName("headingLabel")
        self.lbl_name.setWordWrap(True)
        left.addWidget(self.lbl_name)

        self.lbl_status = QLabel()
        left.addWidget(self.lbl_status)

        info_pairs = [
            ("Estimator", "lbl_estimator"),
            ("Original Bid Date", "lbl_date"),
            ("Accounts", "lbl_customers"),
            ("Won By", "lbl_won_by"),
            ("Notes", "lbl_notes"),
        ]
        for label_text, attr in info_pairs:
            row = QHBoxLayout()
            key = QLabel(f"{label_text}:")
            key.setObjectName("secondaryLabel")
            key.setFixedWidth(120)
            row.addWidget(key)
            val = QLabel()
            val.setWordWrap(True)
            setattr(self, attr, val)
            row.addWidget(val, 1)
            left.addLayout(row)

        left.addStretch()
        main_layout.addLayout(left, 4)

        # --- Right column: revision table ---
        right = QVBoxLayout()
        right.setSpacing(8)

        rev_header = QHBoxLayout()
        rev_header.setContentsMargins(0, 0, 0, 0)
        rev_title = QLabel("Revision History")
        rev_title.setObjectName("subheadingLabel")
        rev_header.addWidget(rev_title)
        rev_header.addStretch()

        self.hide_btn = QPushButton("✕")
        self.hide_btn.setFixedSize(30, 28)
        self.hide_btn.setToolTip("Hide details")
        self.hide_btn.clicked.connect(self.close_requested.emit)
        rev_header.addWidget(self.hide_btn)
        right.addLayout(rev_header)

        self.rev_table = QTableWidget()
        self.rev_table.setColumnCount(6)
        self.rev_table.setHorizontalHeaderLabels([
            "Rev #", "Date", "Bid Total", "Stone SF", "Solid SF", "Reason"
        ])
        self.rev_table.setAlternatingRowColors(True)
        self.rev_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rev_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rev_table.verticalHeader().setVisible(False)
        self.rev_table.setShowGrid(False)

        h = self.rev_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.Stretch)
        self.rev_table.setMinimumHeight(120)

        right.addWidget(self.rev_table)
        main_layout.addLayout(right, 6)

        # --- Action buttons ---
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)
        btn_bar.addStretch()

        self.btn_add_rev = QPushButton("Add Revision")
        self.btn_add_rev.clicked.connect(lambda: self._emit("add_revision"))
        btn_bar.addWidget(self.btn_add_rev)

        self.btn_won = QPushButton("Mark Won")
        self.btn_won.setObjectName("successButton")
        self.btn_won.clicked.connect(lambda: self._emit("mark_won"))
        btn_bar.addWidget(self.btn_won)

        self.btn_link_mw = QPushButton("Link to MW")
        self.btn_link_mw.setToolTip("Link this bid to a Moraware job")
        self.btn_link_mw.clicked.connect(lambda: self._emit("link_mw"))
        btn_bar.addWidget(self.btn_link_mw)

        self.btn_unlink_mw = QPushButton("Unlink from MW")
        self.btn_unlink_mw.setToolTip("Remove Moraware link from this bid")
        self.btn_unlink_mw.clicked.connect(lambda: self._emit("unlink_mw"))
        btn_bar.addWidget(self.btn_unlink_mw)

        self.btn_open_folder = QPushButton("Open Bid Folder")
        self.btn_open_folder.clicked.connect(lambda: self._emit("open_bid_folder"))
        btn_bar.addWidget(self.btn_open_folder)

        self.btn_edit = QPushButton("Edit Bid")
        self.btn_edit.clicked.connect(lambda: self._emit("edit"))
        btn_bar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Delete Bid")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(lambda: self._emit("delete"))
        btn_bar.addWidget(self.btn_delete)

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

        self.lbl_status.setText(bid["status"])
        self.lbl_status.setStyleSheet(get_status_style(bid["status"]))

        self.lbl_estimator.setText(bid["estimator"])

        from datetime import datetime
        try:
            d = datetime.strptime(bid["original_bid_date"], "%Y-%m-%d")
            self.lbl_date.setText(d.strftime("%m/%d/%Y"))
        except (ValueError, TypeError):
            self.lbl_date.setText(bid["original_bid_date"] or "")

        customers = db.get_bid_customers(bid_id)
        self.lbl_customers.setText(", ".join(c["name"] for c in customers) if customers else "—")

        if bid["status"] == "WON" and bid["won_customer_id"]:
            wc = [c for c in customers if c["id"] == bid["won_customer_id"]]
            self.lbl_won_by.setText(wc[0]["name"] if wc else "—")
        else:
            self.lbl_won_by.setText("—")

        self.lbl_notes.setText(bid["notes"] or "—")

        # Disable delete for WON bids
        self.btn_delete.setEnabled(bid["status"] != "WON")

        # Show Unlink only when bid has Moraware link
        self.btn_unlink_mw.setVisible(bool(bid.get("moraware_job_id")))

        # Load revisions
        revisions = db.get_revisions(bid_id)
        self.rev_table.setRowCount(len(revisions))
        for row, rev in enumerate(revisions):
            self.rev_table.setItem(row, 0, QTableWidgetItem(str(rev["revision_no"])))

            try:
                d = datetime.strptime(rev["revision_date"], "%Y-%m-%d")
                date_str = d.strftime("%m/%d/%Y")
            except (ValueError, TypeError):
                date_str = rev["revision_date"] or ""
            self.rev_table.setItem(row, 1, QTableWidgetItem(date_str))

            total_item = QTableWidgetItem(f"${rev['bid_total']:,.2f}" if rev["bid_total"] else "$0.00")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.rev_table.setItem(row, 2, total_item)

            stone_item = QTableWidgetItem(f"{rev['stone_sf']:,.0f}" if rev["stone_sf"] else "0")
            stone_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.rev_table.setItem(row, 3, stone_item)

            solid_item = QTableWidgetItem(f"{rev['solid_surf_sf']:,.0f}" if rev["solid_surf_sf"] else "0")
            solid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.rev_table.setItem(row, 4, solid_item)

            self.rev_table.setItem(row, 5, QTableWidgetItem(rev["reason"] or ""))
            self.rev_table.setRowHeight(row, 36)

        self.show()
