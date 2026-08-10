"""Pick an existing Bid Tracker bid to attach to a Bid Board card."""

from datetime import date, datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


def _fmt_date(raw) -> str:
    text = (raw or "")[:10]
    if len(text) != 10:
        return text or "—"
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return text


class LinkBoardBidDialog(QDialog):
    def __init__(self, db, item_data, parent=None):
        super().__init__(parent)
        self.db = db
        self.item_data = item_data or {}
        self.selected_bid = None
        self._all_rows = []
        self._visible_rows = []
        self._build_ui()
        self._load_rows()

    def _near_date(self) -> str:
        return (
            (self.item_data.get("actual_due_date") or "").strip()
            or (self.item_data.get("board_date") or "").strip()
            or date.today().isoformat()
        )

    def _build_ui(self):
        name = self.item_data.get("bid_name") or "this board item"
        self.setWindowTitle("Link Existing Bid")
        self.setMinimumSize(820, 480)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        intro = QLabel(
            f"Find the Bid Tracker bid that already matches “{name}”. "
            f"Bids near {_fmt_date(self._near_date())} are listed first. "
            "Nothing is linked until you confirm."
        )
        intro.setWordWrap(True)
        intro.setObjectName("secondaryLabel")
        root.addWidget(intro)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by bid name or account…")
        self.search_input.textChanged.connect(self._apply_filters)
        root.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Bid Name", "Date", "Δ days", "Account(s)", "Status"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(lambda _idx: self._accept_selection())
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
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

    def _delta_days(self, row) -> int:
        near = self._near_date()[:10]
        raw = (row.get("original_bid_date") or "")[:10]
        try:
            return abs((date.fromisoformat(raw) - date.fromisoformat(near)).days)
        except ValueError:
            return 99999

    def _load_rows(self):
        item_id = self.item_data.get("id")
        self._all_rows = self.db.find_bids_for_board_link(
            item_id, search="", near_date=self._near_date()
        )
        self._apply_filters()

    def _apply_filters(self):
        q = (self.search_input.text() or "").strip().lower()
        rows = list(self._all_rows)
        if q:
            rows = [
                r for r in rows
                if q in (r.get("bid_name") or "").lower()
                or q in (r.get("customer_names") or "").lower()
                or q in (r.get("estimator") or "").lower()
            ]
        self._visible_rows = rows
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            delta = self._delta_days(r)
            delta_txt = "—" if delta > 9000 else str(delta)
            vals = [
                r.get("bid_name") or "",
                _fmt_date(r.get("original_bid_date")),
                delta_txt,
                r.get("customer_names") or "",
                r.get("status") or "",
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                if c == 2:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, c, item)
        if rows:
            self.table.selectRow(0)
        noun = "bid" if len(rows) == 1 else "bids"
        self.status_label.setText(f"{len(rows)} {noun} — closest dates first.")

    def _accept_selection(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._visible_rows):
            QMessageBox.information(self, "Link Existing Bid", "Select a bid first.")
            return
        bid = self._visible_rows[row]
        board_name = self.item_data.get("bid_name") or "this board item"
        msg = (
            f"Link this existing Bid Tracker bid to “{board_name}”?\n\n"
            f"Bid: {bid.get('bid_name') or '—'}\n"
            f"Date: {_fmt_date(bid.get('original_bid_date'))} "
            f"({self._delta_days(bid)} day(s) from the board date)\n"
            f"Account(s): {bid.get('customer_names') or '—'}\n"
            f"Status: {bid.get('status') or '—'}\n\n"
            "This does not create a new bid. You can unlink later."
        )
        reply = QMessageBox.question(
            self, "Confirm link", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return
        self.selected_bid = bid
        self.accept()
