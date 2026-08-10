"""
Keystone Bid Tracker - Reports Tab
Date range / estimator / status filters, stat cards, win rate,
customer breakdown, monthly volume bar chart, export.
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog, QMessageBox,
    QFrame, QScrollArea, QGridLayout, QDialog, QCheckBox,
    QTextEdit, QGroupBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate, QMarginsF, QSizeF
from PyQt5.QtGui import QTextDocument, QFont, QPageLayout, QPageSize
from PyQt5.QtPrintSupport import QPrinter

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from styles.theme import COLORS, get_status_style


class ReportCard(QFrame):
    """Small summary card used in the report header."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(180)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.value_label = QLabel("—")
        self.value_label.setObjectName("statValue")
        self.value_label.setStyleSheet("font-size: 22px;")
        layout.addWidget(self.value_label)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("statLabel")
        layout.addWidget(self.title_label)

    def set_value(self, val):
        self.value_label.setText(str(val))


def _fit_report_table(table: QTableWidget, max_height: int = 280, row_height: int = 36):
    """Keep report tables readable inside a scroll area (avoid Expanding crush)."""
    table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    table.verticalHeader().setDefaultSectionSize(row_height)
    header_h = max(table.horizontalHeader().height(), 28)
    rows = max(table.rowCount(), 1)
    # Show up to ~7 rows before scrolling inside the table
    visible_rows = min(rows, 7)
    height = header_h + visible_rows * row_height + 6
    table.setFixedHeight(min(max(height, header_h + row_height + 6), max_height))
    for r in range(table.rowCount()):
        table.setRowHeight(r, row_height)


class CustomerBidReportDialog(QDialog):
    """Dialog to select a customer, configure report options, and export as PDF."""

    COL_NUM = 0
    COL_DATE = 1
    COL_NAME = 2
    COL_EST = 3
    COL_TOTAL = 4
    COL_STONE = 5
    COL_SOLID = 6
    COL_STATUS = 7
    COL_NOTES = 8
    NUM_COLS = 9

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_bids = []
        self._current_customer = ""
        self.setWindowTitle("Account Bid Report")
        self.setMinimumSize(950, 650)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("Account Bid Report")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        # --- Filter row: customer + date range ---
        filt_row = QHBoxLayout()
        filt_row.setSpacing(10)

        filt_row.addWidget(QLabel("Account:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(250)
        customers = self.db.get_customers(active_only=False)
        for c in customers:
            self.customer_combo.addItem(c["name"], c["id"])
        filt_row.addWidget(self.customer_combo)

        filt_row.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("MM/dd/yyyy")
        self.date_from.setDate(QDate(2020, 1, 1))
        self.date_from.setMinimumWidth(140)
        filt_row.addWidget(self.date_from)

        filt_row.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("MM/dd/yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMinimumWidth(140)
        filt_row.addWidget(self.date_to)

        load_btn = QPushButton("Load")
        load_btn.setObjectName("primaryButton")
        load_btn.clicked.connect(self._load_report)
        filt_row.addWidget(load_btn)

        filt_row.addStretch()
        layout.addLayout(filt_row)

        # --- Options toggles ---
        opts_row = QHBoxLayout()
        opts_row.setSpacing(16)

        self.chk_date_range = QCheckBox("Show Date Range")
        self.chk_date_range.setChecked(True)
        opts_row.addWidget(self.chk_date_range)

        self.chk_total_bids = QCheckBox("Show Total Bids")
        self.chk_total_bids.setChecked(True)
        opts_row.addWidget(self.chk_total_bids)

        self.chk_won_bids = QCheckBox("Show Won Count")
        self.chk_won_bids.setChecked(True)
        opts_row.addWidget(self.chk_won_bids)

        self.chk_bid_totals = QCheckBox("Show Bid Totals")
        self.chk_bid_totals.setChecked(True)
        opts_row.addWidget(self.chk_bid_totals)

        self.chk_sqft = QCheckBox("Show Sq Ft")
        self.chk_sqft.setChecked(True)
        opts_row.addWidget(self.chk_sqft)

        self.chk_notes = QCheckBox("Show Notes")
        self.chk_notes.setChecked(True)
        opts_row.addWidget(self.chk_notes)

        opts_row.addStretch()
        layout.addLayout(opts_row)

        # --- Summary ---
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("subheadingLabel")
        layout.addWidget(self.summary_label)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(self.NUM_COLS)
        self.table.setHorizontalHeaderLabels([
            "#", "Date", "Bid Name", "Estimator", "Bid Total",
            "Stone SF", "Solid SF", "Status", "Notes"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(self.COL_NUM, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_DATE, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        h.setSectionResizeMode(self.COL_EST, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_TOTAL, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_STONE, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_SOLID, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(self.COL_NOTES, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        # --- General notes ---
        notes_label = QLabel("General Notes (included on PDF):")
        notes_label.setObjectName("secondaryLabel")
        layout.addWidget(notes_label)

        self.general_notes = QTextEdit()
        self.general_notes.setPlaceholderText("Add any general notes to appear at the bottom of the report...")
        self.general_notes.setMaximumHeight(72)
        layout.addWidget(self.general_notes)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.export_btn = QPushButton("Export PDF")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.clicked.connect(self._on_export_pdf)
        btn_row.addWidget(self.export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        if self.customer_combo.count() > 0:
            self._load_report()

    def _load_report(self):
        cust_id = self.customer_combo.currentData()
        cust_name = self.customer_combo.currentText()
        if not cust_id:
            return

        df = self.date_from.date().toString("yyyy-MM-dd")
        dt = self.date_to.date().toString("yyyy-MM-dd")

        bids = self.db.get_bids_for_customer(cust_id, date_from=df, date_to=dt)
        self._current_bids = bids
        self._current_customer = cust_name

        total_bids = len(bids)
        won_count = sum(1 for b in bids if b["status"] == "WON")
        total_value = sum(b.get("bid_total") or 0 for b in bids)
        won_value = sum(b.get("bid_total") or 0 for b in bids if b["status"] == "WON")

        self.summary_label.setText(
            f"{cust_name}: {total_bids} bids, {won_count} awarded "
            f"(${won_value:,.0f} of ${total_value:,.0f} total)"
        )

        self.table.blockSignals(True)
        self.table.setRowCount(len(bids))
        for row, b in enumerate(bids):
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_NUM, num_item)

            try:
                d = datetime.strptime(b["original_bid_date"], "%Y-%m-%d")
                date_str = d.strftime("%m/%d/%Y")
            except (ValueError, TypeError):
                date_str = b.get("original_bid_date") or ""
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_DATE, date_item)

            name_item = QTableWidgetItem(b.get("bid_name") or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_NAME, name_item)

            est_item = QTableWidgetItem(b.get("estimator") or "")
            est_item.setFlags(est_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_EST, est_item)

            total_val = b.get("bid_total") or 0
            total_item = QTableWidgetItem(f"${total_val:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, self.COL_TOTAL, total_item)

            stone_val = b.get("stone_sf") or 0
            stone_item = QTableWidgetItem(f"{stone_val:,.0f}")
            stone_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            stone_item.setFlags(stone_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_STONE, stone_item)

            solid_val = b.get("solid_surf_sf") or 0
            solid_item = QTableWidgetItem(f"{solid_val:,.0f}")
            solid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            solid_item.setFlags(solid_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_SOLID, solid_item)

            status_item = QTableWidgetItem(b["status"])
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_STATUS, status_item)

            notes_item = QTableWidgetItem("")
            self.table.setItem(row, self.COL_NOTES, notes_item)

            self.table.setRowHeight(row, 38)

        self.table.blockSignals(False)

    def _read_table_data(self):
        """Read current table values (including any user edits) for PDF export."""
        rows = []
        for row in range(self.table.rowCount()):
            rows.append({
                "date": self.table.item(row, self.COL_DATE).text() if self.table.item(row, self.COL_DATE) else "",
                "bid_name": self.table.item(row, self.COL_NAME).text() if self.table.item(row, self.COL_NAME) else "",
                "estimator": self.table.item(row, self.COL_EST).text() if self.table.item(row, self.COL_EST) else "",
                "bid_total": self.table.item(row, self.COL_TOTAL).text() if self.table.item(row, self.COL_TOTAL) else "",
                "stone_sf": self.table.item(row, self.COL_STONE).text() if self.table.item(row, self.COL_STONE) else "",
                "solid_sf": self.table.item(row, self.COL_SOLID).text() if self.table.item(row, self.COL_SOLID) else "",
                "status": self.table.item(row, self.COL_STATUS).text() if self.table.item(row, self.COL_STATUS) else "",
                "notes": self.table.item(row, self.COL_NOTES).text() if self.table.item(row, self.COL_NOTES) else "",
            })
        return rows

    def _on_export_pdf(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No bids to export.")
            return

        cust_name = self._current_customer
        default_name = f"Bid Report - {cust_name}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", default_name, "PDF Files (*.pdf)"
        )
        if not path:
            return

        table_rows = self._read_table_data()
        toggles = {
            "date_range": self.chk_date_range.isChecked(),
            "total_bids": self.chk_total_bids.isChecked(),
            "won_bids": self.chk_won_bids.isChecked(),
            "bid_totals": self.chk_bid_totals.isChecked(),
            "sqft": self.chk_sqft.isChecked(),
            "notes": self.chk_notes.isChecked(),
        }
        date_from_str = self.date_from.date().toString("MM/dd/yyyy")
        date_to_str = self.date_to.date().toString("MM/dd/yyyy")
        general_notes = self.general_notes.toPlainText().strip()

        html = self._build_report_html(
            cust_name, table_rows, toggles,
            date_from_str, date_to_str, general_notes,
        )

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)

            page_layout = QPageLayout(
                QPageSize(QPageSize.Letter),
                QPageLayout.Landscape,
                QMarginsF(12, 12, 12, 12),
                QPageLayout.Millimeter,
            )
            printer.setPageLayout(page_layout)

            doc = QTextDocument()
            doc.setDefaultFont(QFont("Segoe UI", 9))
            doc.setHtml(html)
            doc.setPageSize(QSizeF(printer.pageRect(QPrinter.Point).size()))
            doc.print_(printer)

            QMessageBox.information(
                self, "PDF Exported",
                f"Account bid report saved to:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Failed to generate PDF:\n{e}")

    @staticmethod
    def _build_report_html(customer_name, rows, toggles,
                           date_from, date_to, general_notes):
        today = datetime.now().strftime("%m/%d/%Y")
        total_bids = len(rows)
        won_count = sum(1 for r in rows if r["status"] == "WON")

        # --- Header ---
        html = f"""
        <html>
        <body style="font-family: Segoe UI, Arial, sans-serif; color: #333;">
            <h1 style="color:#1a1a1a;margin-bottom:4px;">Keystone Solid Surfaces</h1>
            <h2 style="color:#333;margin-top:0;">Bid Summary for {customer_name}</h2>
            <p style="color:#666;margin-bottom:12px;">Report generated: {today}</p>
        """

        # --- Summary stats ---
        summary_parts = []
        if toggles.get("date_range"):
            summary_parts.append(f"<strong>Date Range:</strong> {date_from} &ndash; {date_to}")
        if toggles.get("total_bids"):
            summary_parts.append(f"<strong>Total Bids:</strong> {total_bids}")
        if toggles.get("won_bids"):
            summary_parts.append(f"<strong>Awarded:</strong> {won_count}")
        if summary_parts:
            html += '<p style="margin-bottom:12px;">' + " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(summary_parts) + "</p>"

        # --- Table header ---
        th_style = 'style="padding:8px 10px;color:#fff;text-align:left;"'
        th_right = 'style="padding:8px 10px;color:#fff;text-align:right;"'
        th_center = 'style="padding:8px 10px;color:#fff;text-align:center;"'

        html += '<table style="width:100%;border-collapse:collapse;border:1px solid #ddd;">'
        html += '<thead><tr style="background-color:#1a1a1a;">'
        html += f'<th {th_style}>Date</th>'
        html += f'<th {th_style}>Bid Name</th>'
        html += f'<th {th_style}>Estimator</th>'
        if toggles.get("bid_totals"):
            html += f'<th {th_right}>Bid Total</th>'
        if toggles.get("sqft"):
            html += f'<th {th_right}>Stone SF</th>'
            html += f'<th {th_right}>Solid SF</th>'
        html += f'<th {th_center}>Status</th>'
        if toggles.get("notes"):
            html += f'<th {th_style}>Notes</th>'
        html += '</tr></thead><tbody>'

        # --- Table rows ---
        td = 'style="padding:6px 10px;"'
        td_right = 'style="padding:6px 10px;text-align:right;"'
        td_center = 'style="padding:6px 10px;text-align:center;"'

        for i, r in enumerate(rows):
            is_won = r["status"] == "WON"
            if is_won:
                row_bg = "#e8f5e9"
                status_html = '<span style="color:#2e7d32;font-weight:bold;">AWARDED</span>'
            else:
                row_bg = "#ffffff" if i % 2 == 0 else "#f5f5f5"
                status_html = f'<span style="color:#666;">{r["status"]}</span>'

            html += f'<tr style="background-color:{row_bg};">'
            html += f'<td {td}>{r["date"]}</td>'
            html += f'<td {td}>{r["bid_name"]}</td>'
            html += f'<td {td}>{r["estimator"]}</td>'
            if toggles.get("bid_totals"):
                html += f'<td {td_right}>{r["bid_total"]}</td>'
            if toggles.get("sqft"):
                html += f'<td {td_right}>{r["stone_sf"]}</td>'
                html += f'<td {td_right}>{r["solid_sf"]}</td>'
            html += f'<td {td_center}>{status_html}</td>'
            if toggles.get("notes"):
                html += f'<td {td}>{r["notes"]}</td>'
            html += '</tr>'

        html += '</tbody></table>'

        # --- General notes ---
        if general_notes:
            escaped = general_notes.replace("\n", "<br/>")
            html += f"""
            <div style="margin-top:16px;padding:10px;border:1px solid #ddd;border-radius:4px;">
                <p style="margin:0 0 4px 0;font-weight:bold;">Notes:</p>
                <p style="margin:0;color:#555;">{escaped}</p>
            </div>"""

        html += """
            <p style="margin-top:16px;color:#666;font-size:11px;">
                Keystone Solid Surfaces &mdash; Confidential
            </p>
        </body>
        </html>"""

        return html


class ReportsTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Reports")
        title.setObjectName("headingLabel")
        header.addWidget(title)
        header.addStretch()

        self.cust_report_btn = QPushButton("Account Bid Report")
        self.cust_report_btn.clicked.connect(self._on_customer_report)
        header.addWidget(self.cust_report_btn)

        self.export_btn = QPushButton("Export Report")
        self.export_btn.clicked.connect(self._on_export)
        header.addWidget(self.export_btn)
        layout.addLayout(header)

        # Filters
        filt = QHBoxLayout()
        filt.setSpacing(10)

        filt.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("MM/dd/yyyy")
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_from.setMinimumWidth(130)
        self.date_from.setFixedWidth(135)
        filt.addWidget(self.date_from)

        filt.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("MM/dd/yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMinimumWidth(130)
        self.date_to.setFixedWidth(135)
        filt.addWidget(self.date_to)

        self.est_combo = QComboBox()
        self.est_combo.setMinimumWidth(140)
        filt.addWidget(self.est_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Status", "PENDING", "BIDDING", "WON"])
        self.status_combo.setMinimumWidth(120)
        filt.addWidget(self.status_combo)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primaryButton")
        apply_btn.clicked.connect(self._run_reports)
        filt.addWidget(apply_btn)

        filt.addStretch()
        layout.addLayout(filt)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Status summary cards row
        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(12)
        self.card_pending = ReportCard("PENDING")
        self.card_won = ReportCard("WON")
        self.card_total_val = ReportCard("TOTAL VALUE")
        for c in (self.card_pending, self.card_won, self.card_total_val):
            self.cards_row.addWidget(c)
        self.cards_row.addStretch()
        self.content_layout.addLayout(self.cards_row)

        # Win rate section
        self.win_rate_label = QLabel("Win Rate: —")
        self.win_rate_label.setObjectName("subheadingLabel")
        self.content_layout.addWidget(self.win_rate_label)

        self.win_rate_table = QTableWidget()
        self.win_rate_table.setColumnCount(4)
        self.win_rate_table.setHorizontalHeaderLabels(["Estimator", "Total Bids", "Won", "Win Rate"])
        self.win_rate_table.setAlternatingRowColors(True)
        self.win_rate_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.win_rate_table.verticalHeader().setVisible(False)
        self.win_rate_table.setShowGrid(False)
        self.win_rate_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        h = self.win_rate_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        _fit_report_table(self.win_rate_table, max_height=220)
        self.content_layout.addWidget(self.win_rate_table)

        # Bids by customer section
        cust_label = QLabel("Bids by Customer")
        cust_label.setObjectName("subheadingLabel")
        self.content_layout.addWidget(cust_label)

        self.cust_table = QTableWidget()
        self.cust_table.setColumnCount(4)
        self.cust_table.setHorizontalHeaderLabels(["Account", "Bids", "Won", "Total Value"])
        self.cust_table.setAlternatingRowColors(True)
        self.cust_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cust_table.verticalHeader().setVisible(False)
        self.cust_table.setShowGrid(False)
        self.cust_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        h2 = self.cust_table.horizontalHeader()
        h2.setSectionResizeMode(0, QHeaderView.Stretch)
        _fit_report_table(self.cust_table, max_height=280)
        self.content_layout.addWidget(self.cust_table)

        loc_label = QLabel("Bids by Location")
        loc_label.setObjectName("subheadingLabel")
        self.content_layout.addWidget(loc_label)

        self.loc_table = QTableWidget()
        self.loc_table.setColumnCount(4)
        self.loc_table.setHorizontalHeaderLabels(["Location", "Bids", "Won", "Total Value"])
        self.loc_table.setAlternatingRowColors(True)
        self.loc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.loc_table.verticalHeader().setVisible(False)
        self.loc_table.setShowGrid(False)
        self.loc_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        h_loc = self.loc_table.horizontalHeader()
        h_loc.setSectionResizeMode(0, QHeaderView.Stretch)
        _fit_report_table(self.loc_table, max_height=280)
        self.content_layout.addWidget(self.loc_table)

        # Monthly volume chart
        chart_label = QLabel("Monthly Bid Volume")
        chart_label.setObjectName("subheadingLabel")
        self.content_layout.addWidget(chart_label)

        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.figure.patch.set_facecolor(COLORS["background"])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(250)
        self.content_layout.addWidget(self.canvas)

        self.content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

    def refresh(self):
        self._refresh_estimator_combo()
        self._run_reports()

    def _refresh_estimator_combo(self):
        current = self.est_combo.currentText()
        self.est_combo.blockSignals(True)
        self.est_combo.clear()
        self.est_combo.addItem("All Estimators")
        for e in self.db.get_estimators():
            self.est_combo.addItem(e)
        idx = self.est_combo.findText(current)
        if idx >= 0:
            self.est_combo.setCurrentIndex(idx)
        self.est_combo.blockSignals(False)

    def _get_filters(self):
        df = self.date_from.date().toString("yyyy-MM-dd")
        dt = self.date_to.date().toString("yyyy-MM-dd")
        est = self.est_combo.currentText()
        if est == "All Estimators":
            est = ""
        status = self.status_combo.currentText()
        if status == "All Status":
            status = ""
        return df, dt, est, status

    def _run_reports(self):
        df, dt, est, status = self._get_filters()

        # Status summary
        by_status = self.db.get_bids_by_status_summary(df, dt, est)
        status_map = {s["status"]: s for s in by_status}
        total_val = sum(s.get("total_value", 0) for s in by_status)

        def _stat(st):
            return status_map.get(st, {})

        pending_cnt = _stat('PENDING').get('cnt', 0) + _stat('BIDDING').get('cnt', 0)
        self.card_pending.set_value(f"{pending_cnt}")
        self.card_won.set_value(f"{_stat('WON').get('cnt', 0)}")
        self.card_total_val.set_value(f"${total_val:,.0f}")

        # Win rate
        win_data = self.db.get_win_rate(df, dt)
        self.win_rate_label.setText(f"Overall Win Rate: {win_data['overall_rate']}%")

        estimators = win_data.get("by_estimator", [])
        self.win_rate_table.setRowCount(len(estimators))
        for row, e in enumerate(estimators):
            self.win_rate_table.setItem(row, 0, QTableWidgetItem(e["estimator"]))
            self.win_rate_table.setItem(row, 1, QTableWidgetItem(str(e["total"])))
            self.win_rate_table.setItem(row, 2, QTableWidgetItem(str(e["won"])))
            self.win_rate_table.setItem(row, 3, QTableWidgetItem(f"{e['rate']}%"))
        _fit_report_table(self.win_rate_table, max_height=220)

        # By customer
        by_cust = self.db.get_bids_by_customer(df, dt, est, status)
        self.cust_table.setRowCount(len(by_cust))
        for row, c in enumerate(by_cust):
            self.cust_table.setItem(row, 0, QTableWidgetItem(c["customer_name"]))
            self.cust_table.setItem(row, 1, QTableWidgetItem(str(c["bid_count"])))
            self.cust_table.setItem(row, 2, QTableWidgetItem(str(c["won_count"])))
            val_item = QTableWidgetItem(f"${c['total_value']:,.0f}")
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cust_table.setItem(row, 3, val_item)
        _fit_report_table(self.cust_table, max_height=280)

        by_loc = self.db.get_bids_by_location(df, dt, est, status)
        self.loc_table.setRowCount(len(by_loc))
        for row, loc in enumerate(by_loc):
            self.loc_table.setItem(row, 0, QTableWidgetItem(loc.get("location_name") or "(No location)"))
            self.loc_table.setItem(row, 1, QTableWidgetItem(str(loc.get("bid_count") or 0)))
            self.loc_table.setItem(row, 2, QTableWidgetItem(str(loc.get("won_count") or 0)))
            val_item = QTableWidgetItem(f"${(loc.get('total_value') or 0):,.0f}")
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.loc_table.setItem(row, 3, val_item)
        _fit_report_table(self.loc_table, max_height=280)

        # Monthly chart
        monthly = self.db.get_monthly_volume(df, dt, est)
        self._draw_chart(monthly)

    def _draw_chart(self, monthly):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(COLORS["surface"])

        if not monthly:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    color=COLORS["text_secondary"], fontsize=14,
                    transform=ax.transAxes)
            self.canvas.draw()
            return

        months = [m["month"] for m in monthly]
        counts = [m["bid_count"] for m in monthly]

        bars = ax.bar(range(len(months)), counts, color=COLORS["accent"], width=0.6)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha="right",
                           color=COLORS["text_secondary"], fontsize=8)
        ax.tick_params(axis="y", colors=COLORS["text_secondary"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(COLORS["border"])
        ax.spines["left"].set_color(COLORS["border"])
        ax.set_ylabel("Bids", color=COLORS["text_secondary"], fontsize=10)

        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(count), ha="center", va="bottom",
                    color=COLORS["text_primary"], fontsize=9)

        self.figure.tight_layout()
        self.canvas.draw()

    def _on_customer_report(self):
        dlg = CustomerBidReportDialog(self.db, self)
        dlg.exec_()

    def _on_export(self):
        try:
            from utils.excel_export import export_report_data
            df, dt, est, status = self._get_filters()

            by_status = [
                s for s in self.db.get_bids_by_status_summary(df, dt, est)
                if s["status"] not in ("LOST", "DEAD")
            ]
            report = {
                "by_status": by_status,
                "by_customer": self.db.get_bids_by_customer(df, dt, est, status),
                "win_rate": self.db.get_win_rate(df, dt),
            }

            path, _ = QFileDialog.getSaveFileName(
                self, "Export Report", "report.xlsx",
                "Excel Files (*.xlsx)",
            )
            if path:
                export_report_data(report, path)
                QMessageBox.information(self, "Export Complete", f"Report exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
