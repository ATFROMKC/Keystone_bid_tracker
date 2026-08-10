"""Confirm Outlook-suggested due dates and existing accounts after sync."""

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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


class OutlookHintReviewDialog(QDialog):
    """Batch-confirm suggested due dates / accounts. Never creates new accounts."""

    def __init__(self, candidates, parent=None):
        super().__init__(parent)
        self.candidates = [dict(c) for c in (candidates or [])]
        self.accepted_applies = []
        self.setWindowTitle("Review Outlook suggestions")
        self.setMinimumSize(820, 420)
        self.setModal(True)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        intro = QLabel(
            "Sync found possible due dates and accounts from Outlook text. "
            "Check the rows you want to apply. Unmatched emails are shown for "
            "reference only — no new accounts are created."
        )
        intro.setWordWrap(True)
        intro.setObjectName("secondaryLabel")
        root.addWidget(intro)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Apply", "Bid", "Board date", "Suggested due", "Suggested accounts", "Unmatched emails"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        h.setSectionResizeMode(5, QHeaderView.Stretch)
        root.addWidget(self.table, 1)

        btns = QHBoxLayout()
        btns.addStretch()
        skip = QPushButton("Skip all")
        skip.clicked.connect(self.reject)
        btns.addWidget(skip)
        apply = QPushButton("Apply selected")
        apply.setObjectName("primaryButton")
        apply.clicked.connect(self._apply_selected)
        btns.addWidget(apply)
        root.addLayout(btns)

    def _populate(self):
        self.table.setRowCount(len(self.candidates))
        for i, c in enumerate(self.candidates):
            apply_item = QTableWidgetItem()
            apply_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            can_apply = bool(c.get("apply_due") or c.get("apply_accounts"))
            apply_item.setCheckState(Qt.Checked if can_apply else Qt.Unchecked)
            if not can_apply:
                apply_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, apply_item)
            self.table.setItem(i, 1, QTableWidgetItem(c.get("bid_name") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(_fmt_date(c.get("board_date"))))
            due = c.get("suggested_due_date") if c.get("apply_due") else None
            self.table.setItem(i, 3, QTableWidgetItem(_fmt_date(due) if due else "—"))
            names = ", ".join(c.get("suggested_customer_names") or []) if c.get("apply_accounts") else ""
            self.table.setItem(i, 4, QTableWidgetItem(names or "—"))
            emails = ", ".join(c.get("unmatched_emails") or [])
            self.table.setItem(i, 5, QTableWidgetItem(emails or "—"))
            self.table.setRowHeight(i, 40)

    def _apply_selected(self):
        self.accepted_applies = []
        for i, c in enumerate(self.candidates):
            item = self.table.item(i, 0)
            if item is None or item.checkState() != Qt.Checked:
                continue
            self.accepted_applies.append({
                "item_id": c["item_id"],
                "actual_due_date": c.get("suggested_due_date") if c.get("apply_due") else None,
                "customer_ids": list(c.get("suggested_customer_ids") or []) if c.get("apply_accounts") else [],
            })
        self.accept()
