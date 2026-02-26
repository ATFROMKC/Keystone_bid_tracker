"""
Keystone Bid Tracker - Accounts Tab
Manage account list: add, edit, toggle active, search.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QInputDialog,
    QAbstractItemView, QDialog, QComboBox, QFormLayout,
)
from PyQt5.QtCore import Qt


class MergeCustomersDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.merge_from_id = None
        self.merge_into_id = None
        self.setWindowTitle("Merge Accounts")
        self.setMinimumSize(440, 300)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Merge Accounts")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.from_combo = QComboBox()
        self.to_combo = QComboBox()

        customers = self.db.get_customers()
        for c in customers:
            bid_count = self.db.get_customer_bid_count(c["id"])
            label = f"{c['name']} ({bid_count})"
            self.from_combo.addItem(label, c["id"])
            self.to_combo.addItem(label, c["id"])

        form.addRow("Merge From (delete):", self.from_combo)
        form.addRow("Merge Into (keep):", self.to_combo)
        layout.addLayout(form)

        warning = QLabel(
            "All bids from the Merge From account will be reassigned to "
            "Merge Into. The Merge From account will be permanently deleted."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #ff9800; font-size: 12px; padding: 8px 0;")
        layout.addWidget(warning)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm Merge")
        confirm_btn.setObjectName("dangerButton")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

    def _on_confirm(self):
        if self.from_combo.count() == 0 or self.to_combo.count() == 0:
            QMessageBox.warning(self, "Error", "Both accounts must be selected.")
            return

        from_id = self.from_combo.currentData()
        into_id = self.to_combo.currentData()

        if from_id == into_id:
            QMessageBox.warning(self, "Error", "Cannot merge an account into itself.\nSelect two different accounts.")
            return

        self.merge_from_id = from_id
        self.merge_into_id = into_id
        self.accept()


class CustomersTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header row
        header = QHBoxLayout()
        title = QLabel("Accounts")
        title.setObjectName("headingLabel")
        header.addWidget(title)
        header.addStretch()

        self.merge_btn = QPushButton("Merge Accounts")
        self.merge_btn.clicked.connect(self._on_merge)
        header.addWidget(self.merge_btn)

        self.add_btn = QPushButton("+ Add Account")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(self._on_add)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # Search
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search accounts...")
        self.search_input.setMaximumWidth(350)
        self.search_input.textChanged.connect(self.refresh)
        search_row.addWidget(self.search_input)
        search_row.addStretch()

        self.count_label = QLabel()
        self.count_label.setObjectName("secondaryLabel")
        search_row.addWidget(self.count_label)
        layout.addLayout(search_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Bids", "Status", ""])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(300)

        layout.addWidget(self.table)

    def refresh(self):
        search = self.search_input.text().strip()
        customers = self.db.get_customers(search=search)

        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            bid_count = self.db.get_customer_bid_count(c["id"])

            name_item = QTableWidgetItem(c["name"])
            name_item.setData(Qt.UserRole, c["id"])
            self.table.setItem(row, 0, name_item)

            count_item = QTableWidgetItem(str(bid_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, count_item)

            status_text = "Active" if c["active"] else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            if not c["active"]:
                status_item.setForeground(Qt.gray)
            self.table.setItem(row, 2, status_item)

            # Actions cell with buttons
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(60)
            edit_btn.setProperty("customer_id", c["id"])
            edit_btn.setProperty("customer_name", c["name"])
            edit_btn.clicked.connect(self._on_edit)
            actions_layout.addWidget(edit_btn)

            toggle_btn = QPushButton("Deactivate" if c["active"] else "Activate")
            toggle_btn.setFixedWidth(90)
            toggle_btn.setProperty("customer_id", c["id"])
            toggle_btn.clicked.connect(self._on_toggle)
            actions_layout.addWidget(toggle_btn)

            self.table.setCellWidget(row, 3, actions)
            self.table.setRowHeight(row, 44)

        self.count_label.setText(f"{len(customers)} account{'s' if len(customers) != 1 else ''}")

    def _on_add(self):
        name, ok = QInputDialog.getText(self, "Add Account", "Account name:")
        if ok and name.strip():
            existing = self.db.get_customer_by_name(name.strip())
            if existing:
                QMessageBox.warning(self, "Duplicate", f"Account '{name.strip()}' already exists.")
                return
            self.db.add_customer(name.strip())
            self.refresh()

    def _on_edit(self):
        btn = self.sender()
        cid = btn.property("customer_id")
        old_name = btn.property("customer_name")
        name, ok = QInputDialog.getText(self, "Edit Account", "Account name:", text=old_name)
        if ok and name.strip() and name.strip() != old_name:
            existing = self.db.get_customer_by_name(name.strip())
            if existing and existing["id"] != cid:
                QMessageBox.warning(self, "Duplicate", f"Account '{name.strip()}' already exists.")
                return
            self.db.update_customer(cid, name.strip())
            self.refresh()

    def _on_toggle(self):
        btn = self.sender()
        cid = btn.property("customer_id")
        self.db.toggle_customer_active(cid)
        self.refresh()

    def _on_merge(self):
        dlg = MergeCustomersDialog(self.db, self)
        if dlg.exec_() and dlg.merge_from_id is not None:
            self.db.merge_customers(dlg.merge_from_id, dlg.merge_into_id)
            self.refresh()
