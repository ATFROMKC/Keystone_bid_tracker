"""
Keystone Bid Tracker - PM Completed History Tab
Monthly completed trends from Moraware-linked invoice data.
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import QTimer


def _fmt_month(month_key: str):
    if not month_key:
        return "—"
    try:
        return datetime.strptime(month_key, "%Y-%m-%d").strftime("%b %Y")
    except (ValueError, TypeError):
        return str(month_key)


def _fmt_money(value):
    return f"${float(value or 0):,.0f}"


def _fmt_sqft(value):
    return f"{float(value or 0):,.0f} SF"


class PMHistoryTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Completed History")
        title.setObjectName("headingLabel")
        layout.addWidget(title)
        subtitle = QLabel("Monthly revenue and square-foot trends from completed invoice phases")
        subtitle.setObjectName("secondaryLabel")
        layout.addWidget(subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Month", "Revenue", "Solid Surface SF", "Stone SF"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        layout.addStretch()

    def refresh(self):
        rows = self.db.get_pm_completed_history(limit=24)
        self.table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(_fmt_month(item.get("month", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(_fmt_money(item.get("revenue", 0))))
            self.table.setItem(row, 2, QTableWidgetItem(_fmt_sqft(item.get("solid_surf_sf", 0))))
            self.table.setItem(row, 3, QTableWidgetItem(_fmt_sqft(item.get("stone_sf", 0))))
