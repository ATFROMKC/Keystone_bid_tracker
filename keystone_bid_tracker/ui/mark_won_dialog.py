"""
Keystone Bid Tracker - Mark Won Dialog
Select the winning customer and optional won details.
Supports edit_mode for re-opening with pre-filled values.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QLineEdit, QTextEdit, QDateEdit,
    QInputDialog,
)
from PyQt5.QtCore import Qt, QDate


class MarkWonDialog(QDialog):
    def __init__(self, db, bid_id, parent=None, edit_mode=False):
        super().__init__(parent)
        self.db = db
        self.bid_id = bid_id
        self.edit_mode = edit_mode
        self.selected_customer_id = None
        self.salesperson = ""
        self.project_manager = ""
        self.won_date = ""
        self.moraware_job_date = ""
        self.won_notes = ""

        self.bid = self.db.get_bid_by_id(bid_id)
        self.setWindowTitle("Edit Won Details" if edit_mode else "Mark Bid Won")
        self.setMinimumSize(420, 420)
        self.setModal(True)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        title = QLabel("Edit Won Details" if self.edit_mode else "Mark Bid Won")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        bid_label = QLabel(self.bid["bid_name"])
        bid_label.setObjectName("subheadingLabel")
        layout.addWidget(bid_label)

        layout.addSpacing(4)

        label = QLabel("Winning account:")
        layout.addWidget(label)

        cust_row = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setSizePolicy(self.combo.sizePolicy())
        customers = self.db.get_bid_customers(self.bid_id)
        for c in customers:
            self.combo.addItem(c["name"], c["id"])
        if self.edit_mode and self.bid.get("won_customer_id"):
            idx = self.combo.findData(self.bid["won_customer_id"])
            if idx >= 0:
                self.combo.setCurrentIndex(idx)
        cust_row.addWidget(self.combo, 1)

        add_cust_btn = QPushButton("+ Add Account")
        add_cust_btn.setObjectName("secondaryButton")
        add_cust_btn.clicked.connect(self._on_add_customer)
        cust_row.addWidget(add_cust_btn)
        layout.addLayout(cust_row)

        layout.addSpacing(4)

        sp_label = QLabel("Salesperson:")
        sp_label.setObjectName("secondaryLabel")
        layout.addWidget(sp_label)
        self.salesperson_input = QComboBox()
        self.salesperson_input.setEditable(True)
        self.salesperson_input.setInsertPolicy(QComboBox.NoInsert)
        self.salesperson_input.addItem("")
        for sp in self.db.get_salespersons():
            self.salesperson_input.addItem(sp)
        self.salesperson_input.setCurrentText("")
        layout.addWidget(self.salesperson_input)

        pm_label = QLabel("Project Manager:")
        pm_label.setObjectName("secondaryLabel")
        layout.addWidget(pm_label)
        self.pm_input = QComboBox()
        self.pm_input.setEditable(True)
        self.pm_input.setInsertPolicy(QComboBox.NoInsert)
        self.pm_input.addItem("")
        for pm in self.db.get_project_managers():
            self.pm_input.addItem(pm)
        self.pm_input.setCurrentText("")
        layout.addWidget(self.pm_input)

        date_label = QLabel("Date Won:")
        date_label.setObjectName("secondaryLabel")
        layout.addWidget(date_label)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("MM/dd/yyyy")
        layout.addWidget(self.date_edit)

        notes_label = QLabel("Won Notes:")
        notes_label.setObjectName("secondaryLabel")
        layout.addWidget(notes_label)
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional notes about this win...")
        self.notes_input.setMaximumHeight(72)
        layout.addWidget(self.notes_input)

        if self.edit_mode:
            self.salesperson_input.setCurrentText(self.bid.get("salesperson") or "")
            self.pm_input.setCurrentText(self.bid.get("project_manager") or "")
            if self.bid.get("won_date"):
                d = QDate.fromString(self.bid["won_date"], "yyyy-MM-dd")
                if d.isValid():
                    self.date_edit.setDate(d)
            self.notes_input.setPlainText(self.bid.get("won_notes") or "")

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_text = "Save Changes" if self.edit_mode else "Confirm Won"
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName("successButton")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

    def _on_add_customer(self):
        name, ok = QInputDialog.getText(self, "Add Account", "Account name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if self.combo.findText(name, Qt.MatchFixedString) >= 0:
            QMessageBox.information(self, "Exists", f"'{name}' is already in the list.")
            return
        cust_id = self.db.add_customer(name)
        with self.db._conn() as conn:
            conn.execute(
                "INSERT INTO bid_customers (bid_id, customer_id) VALUES (?, ?)",
                (self.bid_id, cust_id),
            )
        self.combo.addItem(name, cust_id)
        self.combo.setCurrentIndex(self.combo.count() - 1)

    def _on_confirm(self):
        if self.combo.count() == 0:
            QMessageBox.warning(self, "Error", "No accounts linked to this bid.")
            return
        self.selected_customer_id = self.combo.currentData()
        self.salesperson = self.salesperson_input.currentText().strip()
        self.project_manager = self.pm_input.currentText().strip()
        self.won_date = self.date_edit.date().toString("yyyy-MM-dd")
        # Backward-compatible alias for older call sites.
        self.moraware_job_date = self.won_date
        self.won_notes = self.notes_input.toPlainText().strip()
        self.accept()
