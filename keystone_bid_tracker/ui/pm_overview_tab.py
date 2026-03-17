"""
Keystone Bid Tracker - PM Pipeline Tab
Pipeline forecast view based on Moraware-synced invoice data.
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
)
from PyQt5.QtCore import QTimer, Qt

from ui.awarded_tab import PMEditJobDialog

def _fmt_money(value):
    return f"${float(value or 0):,.0f}"


def _fmt_sqft(value):
    return f"{float(value or 0):,.0f} SF"


def _fmt_month(month_key: str):
    if not month_key:
        return "—"
    try:
        return datetime.strptime(month_key, "%Y-%m-%d").strftime("%b %Y")
    except (ValueError, TypeError):
        return str(month_key)


def _fmt_date(date_key: str):
    if not date_key:
        return "—"
    try:
        return datetime.strptime(date_key, "%Y-%m-%d").strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return str(date_key)


class _StatCard(QFrame):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.value_label)
        self.text_label = QLabel(label_text)
        self.text_label.setObjectName("statLabel")
        layout.addWidget(self.text_label)

    def set_value(self, text):
        self.value_label.setText(str(text))


class PMOverviewTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("Pipeline Forecast")
        title.setObjectName("headingLabel")
        root.addWidget(title)
        sub = QLabel("Moraware-linked jobs only (Needs Sync tracked separately)")
        sub.setObjectName("secondaryLabel")
        root.addWidget(sub)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_in_progress = _StatCard("IN PROGRESS ($)")
        self.card_unscheduled = _StatCard("UNSCHEDULED ($)")
        self.card_needs_sync = _StatCard("NEEDS SYNC JOBS")
        for card in (
            self.card_in_progress,
            self.card_unscheduled,
            self.card_needs_sync,
        ):
            cards.addWidget(card)
        root.addLayout(cards)

        plus90_row = QHBoxLayout()
        plus90_row.setSpacing(12)
        self.plus90_confirmed = _StatCard("90+ CONFIRMED START ($ / SF)")
        self.plus90_estimated = _StatCard("90+ ESTIMATED START ($ / SF)")
        plus90_row.addWidget(self.plus90_confirmed)
        plus90_row.addWidget(self.plus90_estimated)
        plus90_row.addStretch()
        root.addLayout(plus90_row)

        self.forecast_label = QLabel("Rolling 90-Day Forecast")
        self.forecast_label.setObjectName("subheadingLabel")
        root.addWidget(self.forecast_label)

        self.forecast_table = QTableWidget()
        self.forecast_table.setColumnCount(5)
        self.forecast_table.setHorizontalHeaderLabels(
            [
                "Month",
                "Start Confirmed ($, SS/ST)",
                "Start Confirmed (SS/ST SF)",
                "Start Estimated ($, SS/ST)",
                "Start Estimated (SS/ST SF)",
            ]
        )
        self.forecast_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.forecast_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.forecast_table.verticalHeader().setVisible(False)
        self.forecast_table.setShowGrid(False)
        fh = self.forecast_table.horizontalHeader()
        fh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, 5):
            fh.setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        root.addWidget(self.forecast_table)

        unscheduled_label = QLabel("Unscheduled Jobs (No Template Date in Moraware)")
        unscheduled_label.setObjectName("subheadingLabel")
        root.addWidget(unscheduled_label)
        self.unscheduled_table = QTableWidget()
        self.unscheduled_table.setColumnCount(5)
        self.unscheduled_table.setHorizontalHeaderLabels(
            ["Bid", "PM", "Dollars", "Sq Ft", "Est. Start Month"]
        )
        self.unscheduled_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.unscheduled_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.unscheduled_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.unscheduled_table.verticalHeader().setVisible(False)
        self.unscheduled_table.setShowGrid(False)
        self.unscheduled_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.unscheduled_table.customContextMenuRequested.connect(self._show_unscheduled_context_menu)
        uh = self.unscheduled_table.horizontalHeader()
        uh.setSectionResizeMode(0, QHeaderView.Stretch)
        uh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        uh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        uh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        uh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        root.addWidget(self.unscheduled_table)

        self.needs_sync_label = QLabel("Needs Sync")
        self.needs_sync_label.setObjectName("subheadingLabel")
        root.addWidget(self.needs_sync_label)
        self.needs_sync_table = QTableWidget()
        self.needs_sync_table.setColumnCount(3)
        self.needs_sync_table.setHorizontalHeaderLabels(["Bid", "PM", "Reason"])
        self.needs_sync_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.needs_sync_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.needs_sync_table.verticalHeader().setVisible(False)
        self.needs_sync_table.setShowGrid(False)
        nh = self.needs_sync_table.horizontalHeader()
        nh.setSectionResizeMode(0, QHeaderView.Stretch)
        nh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        nh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        root.addWidget(self.needs_sync_table)
        root.addStretch()

    def refresh(self):
        payload = self.db.get_pm_pipeline_forecast(days_ahead=90) or {}
        forecast = payload.get("pipeline_forecast", {})
        backlog = forecast.get("backlog", {})
        monthly = forecast.get("monthly_forecast", {})
        months = forecast.get("forecast_months", [])
        unscheduled = forecast.get("unscheduled_jobs", [])
        needs_sync = payload.get("needs_sync", [])
        window_start = forecast.get("window_start", "")
        window_end = forecast.get("window_end", "")
        plus_90 = forecast.get("plus_90", {})

        self.card_in_progress.set_value(
            _fmt_money(backlog.get("In Progress", {}).get("dollars", 0))
        )
        self.card_unscheduled.set_value(
            _fmt_money(backlog.get("Unscheduled", {}).get("dollars", 0))
        )
        self.card_needs_sync.set_value(str(len(needs_sync)))
        self.plus90_confirmed.set_value(
            f"{_fmt_money(plus_90.get('start_confirmed_dollars', 0))} / {_fmt_sqft(plus_90.get('start_confirmed_sq_ft', 0))}"
        )
        self.plus90_estimated.set_value(
            f"{_fmt_money(plus_90.get('start_estimated_dollars', 0))} / {_fmt_sqft(plus_90.get('start_estimated_sq_ft', 0))}"
        )

        if window_start and window_end:
            self.forecast_label.setText(
                f"Rolling 90-Day Forecast ({_fmt_date(window_start)} - {_fmt_date(window_end)})"
            )
        else:
            self.forecast_label.setText("Rolling 90-Day Forecast")

        self.forecast_table.setRowCount(len(months))
        for row, month_key in enumerate(months):
            bucket = monthly.get(month_key, {})
            self.forecast_table.setItem(row, 0, QTableWidgetItem(_fmt_month(month_key)))
            self.forecast_table.setItem(
                row, 1, QTableWidgetItem(_fmt_money(bucket.get("start_confirmed_dollars", 0)))
            )
            self.forecast_table.setItem(
                row, 2, QTableWidgetItem(_fmt_sqft(bucket.get("start_confirmed_sq_ft", 0)))
            )
            self.forecast_table.setItem(
                row, 3, QTableWidgetItem(_fmt_money(bucket.get("start_estimated_dollars", 0)))
            )
            self.forecast_table.setItem(
                row, 4, QTableWidgetItem(_fmt_sqft(bucket.get("start_estimated_sq_ft", 0)))
            )

        self.unscheduled_table.setRowCount(len(unscheduled))
        for row, job in enumerate(unscheduled):
            bid_item = QTableWidgetItem(job.get("bid_name", ""))
            bid_item.setData(Qt.UserRole, job.get("bid_id"))
            self.unscheduled_table.setItem(row, 0, bid_item)
            self.unscheduled_table.setItem(row, 1, QTableWidgetItem(job.get("project_manager", "")))
            self.unscheduled_table.setItem(row, 2, QTableWidgetItem(_fmt_money(job.get("dollars", 0))))
            self.unscheduled_table.setItem(row, 3, QTableWidgetItem(_fmt_sqft(job.get("sq_ft", 0))))
            self.unscheduled_table.setItem(row, 4, QTableWidgetItem(job.get("est_start_month", "") or "—"))

        self.needs_sync_label.setText(f"Needs Sync ({len(needs_sync)})")
        self.needs_sync_table.setRowCount(len(needs_sync))
        for row, job in enumerate(needs_sync):
            self.needs_sync_table.setItem(row, 0, QTableWidgetItem(job.get("bid_name", "")))
            self.needs_sync_table.setItem(row, 1, QTableWidgetItem(job.get("project_manager", "")))
            self.needs_sync_table.setItem(row, 2, QTableWidgetItem(job.get("reason", "")))

    def _show_unscheduled_context_menu(self, pos):
        idx = self.unscheduled_table.indexAt(pos)
        row = idx.row()
        if row < 0:
            return
        bid_item = self.unscheduled_table.item(row, 0)
        bid_id = bid_item.data(Qt.UserRole) if bid_item else None
        if not bid_id:
            return

        self.unscheduled_table.selectRow(row)
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Job")
        chosen = menu.exec_(self.unscheduled_table.viewport().mapToGlobal(pos))
        if chosen == edit_action:
            self._edit_job_from_pipeline(bid_id)

    def _edit_job_from_pipeline(self, bid_id):
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
            self.refresh()
