"""
Keystone Bid Tracker - Import Tab
File picker, preview table, progress bar, import summary.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QProgressBar,
    QMessageBox, QHeaderView, QAbstractItemView, QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class ImportWorker(QThread):
    """Run import in background thread so UI stays responsive."""
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, db, parsed_rows, import_duplicates=False):
        super().__init__()
        self.db = db
        self.parsed_rows = parsed_rows
        self.import_duplicates = import_duplicates

    def run(self):
        try:
            from utils.excel_import import run_import
            result = run_import(
                self.db,
                self.parsed_rows,
                self._on_progress,
                import_duplicates=self.import_duplicates,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current, total):
        self.progress.emit(current, total)


class ImportTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._parsed = []
        self._row_analysis = []
        self._duplicate_count = 0
        self._invalid_date_count = 0
        self._no_customer_count = 0
        self._clean_count = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Import Bids from Excel")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        desc = QLabel("Import historical bid data from a Backlog spreadsheet (.xlsx)")
        desc.setObjectName("secondaryLabel")
        layout.addWidget(desc)

        # File picker row
        file_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("secondaryLabel")
        file_row.addWidget(self.file_label, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        file_row.addWidget(browse_btn)

        self.preview_btn = QPushButton("Preview Import")
        self.preview_btn.setObjectName("primaryButton")
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self._on_preview)
        file_row.addWidget(self.preview_btn)
        layout.addLayout(file_row)

        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(8)
        self.preview_table.setHorizontalHeaderLabels([
            "Bid Date", "Estimator", "Bid Name", "Bid Total",
            "Solid SF", "Stone SF", "Accounts", "Status"
        ])
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setShowGrid(False)
        h = self.preview_table.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(6, QHeaderView.Stretch)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        layout.addWidget(self.preview_table, 1)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat("%v / %m rows")
        self.progress.hide()
        layout.addWidget(self.progress)

        # Summary label
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.hide()
        layout.addWidget(self.summary_label)

        # Run import button
        btn_row = QHBoxLayout()
        self.import_duplicates_cb = QCheckBox("Import duplicates anyway")
        self.import_duplicates_cb.setVisible(False)
        self.import_duplicates_cb.setEnabled(False)
        btn_row.addWidget(self.import_duplicates_cb)
        btn_row.addStretch()
        self.run_btn = QPushButton("Run Import")
        self.run_btn.setObjectName("primaryButton")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._on_run_import)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

        self._filepath = ""

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "",
            "Excel Files (*.xlsx *.xls)"
        )
        if path:
            self._filepath = path
            self.file_label.setText(path)
            self.preview_btn.setEnabled(True)
            self.run_btn.setEnabled(False)
            self.import_duplicates_cb.setChecked(False)
            self.import_duplicates_cb.setVisible(False)
            self.import_duplicates_cb.setEnabled(False)
            self._row_analysis = []
            self._duplicate_count = 0
            self._invalid_date_count = 0
            self._no_customer_count = 0
            self._clean_count = 0
            self.summary_label.hide()

    def _on_preview(self):
        if not self._filepath:
            return
        try:
            from utils.excel_import import preview_import, analyze_rows
            self._parsed = preview_import(self._filepath)
            self._row_analysis = analyze_rows(self.db, self._parsed)
            self._duplicate_count = sum(1 for r in self._row_analysis if r["is_duplicate"])
            self._invalid_date_count = sum(1 for r in self._row_analysis if not r["has_valid_date"])
            self._no_customer_count = sum(1 for r in self._row_analysis if not r["has_customers"])
            self._clean_count = sum(1 for r in self._row_analysis if len(r["reasons"]) == 0)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to read file:\n{e}")
            return

        self.preview_table.setRowCount(len(self._parsed))
        for row, r in enumerate(self._parsed):
            row_info = self._row_analysis[row] if row < len(self._row_analysis) else {
                "is_duplicate": False,
                "has_valid_date": bool(r["bid_date"]),
                "has_customers": len(r["customers"]) > 0,
                "reasons": [],
            }
            reasons = row_info["reasons"]
            self.preview_table.setItem(row, 0, QTableWidgetItem(r["bid_date"]))
            self.preview_table.setItem(row, 1, QTableWidgetItem(r["estimator"]))
            self.preview_table.setItem(row, 2, QTableWidgetItem(r["bid_name"]))
            total_item = QTableWidgetItem(f"${r['bid_total']:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.preview_table.setItem(row, 3, total_item)
            self.preview_table.setItem(row, 4, QTableWidgetItem(f"{r['solid_surf_sf']:,.0f}"))
            self.preview_table.setItem(row, 5, QTableWidgetItem(f"{r['stone_sf']:,.0f}"))
            self.preview_table.setItem(row, 6, QTableWidgetItem(", ".join(r["customers"])))
            status_item = QTableWidgetItem(", ".join(reasons) if reasons else "New")
            self.preview_table.setItem(row, 7, status_item)

            if reasons:
                row_color = Qt.yellow if reasons == ["Duplicate"] else Qt.lightGray
                for col in range(self.preview_table.columnCount()):
                    item = self.preview_table.item(row, col)
                    if item:
                        item.setData(Qt.BackgroundRole, row_color)

            self.preview_table.setRowHeight(row, 36)

        self.run_btn.setEnabled(len(self._parsed) > 0)
        has_duplicates = self._duplicate_count > 0
        self.import_duplicates_cb.setVisible(has_duplicates)
        self.import_duplicates_cb.setEnabled(has_duplicates)
        if not has_duplicates:
            self.import_duplicates_cb.setChecked(False)

        self.summary_label.setText(
            f"{len(self._parsed)} rows ready to import.\n"
            f"{self._clean_count} new, "
            f"{self._duplicate_count} duplicate, "
            f"{self._invalid_date_count} invalid date, "
            f"{self._no_customer_count} no customer."
        )
        self.summary_label.show()

    def _on_run_import(self):
        if not self._parsed:
            return

        import_duplicates = self.import_duplicates_cb.isChecked()
        if self._duplicate_count > 0:
            if import_duplicates:
                confirm_text = (
                    f"Import {len(self._parsed)} rows?\n"
                    f"{self._duplicate_count} duplicates detected.\n"
                    "Duplicates will be imported."
                )
            else:
                confirm_text = (
                    f"Import {len(self._parsed)} rows?\n"
                    f"{self._duplicate_count} duplicates detected.\n"
                    "Duplicates will be skipped."
                )
        else:
            confirm_text = f"Import {len(self._parsed)} rows?"

        reply = QMessageBox.question(
            self,
            "Confirm Import",
            confirm_text,
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.run_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.progress.setMaximum(len(self._parsed))
        self.progress.setValue(0)
        self.progress.show()

        self._worker = ImportWorker(self.db, self._parsed, import_duplicates=import_duplicates)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_import_done)
        self._worker.error.connect(self._on_import_error)
        self._worker.start()

    def _on_progress(self, current, total):
        self.progress.setValue(current)

    def _on_import_done(self, result):
        self.progress.hide()
        self.summary_label.setText(
            f"Import complete!\n"
            f"{result['imported']} bids imported, "
            f"{result['customers_created']} customers created, "
            f"{result['skipped']} skipped (duplicates or invalid)."
        )
        self.summary_label.setStyleSheet("color: #4caf50; font-size: 14px; font-weight: 600;")
        self.summary_label.show()
        self._parsed = []
        self._row_analysis = []
        self._duplicate_count = 0
        self._invalid_date_count = 0
        self._no_customer_count = 0
        self._clean_count = 0
        self.import_duplicates_cb.setChecked(False)
        self.import_duplicates_cb.setVisible(False)
        self.import_duplicates_cb.setEnabled(False)
        self.run_btn.setEnabled(False)

    def _on_import_error(self, msg):
        self.progress.hide()
        QMessageBox.critical(self, "Import Error", msg)
        self.run_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.import_duplicates_cb.setEnabled(self._duplicate_count > 0)

    def refresh(self):
        pass
