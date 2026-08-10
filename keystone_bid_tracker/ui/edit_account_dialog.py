"""
Keystone Bid Tracker - Edit Account dialog
Edit account name and manage reusable email contacts for that account.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QWidget, QInputDialog,
)
from PyQt5.QtCore import Qt


class EditAccountDialog(QDialog):
    def __init__(self, db, customer, parent=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.setWindowTitle("Edit Account")
        self.setMinimumSize(560, 480)
        self.setModal(True)
        self._build_ui()
        self._load_contacts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("Edit Account")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        form = QFormLayout()
        self.name_input = QLineEdit(self.customer.get("name", ""))
        form.addRow("Account name *", self.name_input)
        layout.addLayout(form)

        emails_label = QLabel("Email contacts")
        emails_label.setObjectName("subheadingLabel")
        layout.addWidget(emails_label)

        hint = QLabel(
            "These emails are reusable. On a Bid Board item you can pick which "
            "ones the bid invite should go to."
        )
        hint.setObjectName("secondaryLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Email", ""])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        add_row = QHBoxLayout()
        self.contact_name_input = QLineEdit()
        self.contact_name_input.setPlaceholderText("Contact name (optional)")
        add_row.addWidget(self.contact_name_input)
        self.contact_email_input = QLineEdit()
        self.contact_email_input.setPlaceholderText("email@company.com")
        add_row.addWidget(self.contact_email_input, 1)
        add_btn = QPushButton("+ Add email")
        add_btn.clicked.connect(self._on_add_contact)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save Account")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _load_contacts(self):
        contacts = self.db.get_customer_contacts(self.customer["id"])
        self.table.setRowCount(len(contacts))
        for row, c in enumerate(contacts):
            self.table.setItem(row, 0, QTableWidgetItem(c.get("name") or ""))
            self.table.setItem(row, 1, QTableWidgetItem(c.get("email") or ""))
            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(4)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(56)
            edit_btn.clicked.connect(lambda _, cid=c["id"], cc=c: self._on_edit_contact(cid, cc))
            al.addWidget(edit_btn)
            del_btn = QPushButton("Remove")
            del_btn.setFixedWidth(70)
            del_btn.clicked.connect(lambda _, cid=c["id"]: self._on_delete_contact(cid))
            al.addWidget(del_btn)
            self.table.setCellWidget(row, 2, actions)
            self.table.setRowHeight(row, 40)

    def _on_add_contact(self):
        email = self.contact_email_input.text().strip()
        name = self.contact_name_input.text().strip()
        if not email or "@" not in email:
            QMessageBox.warning(self, "Invalid email", "Enter a valid email address.")
            return
        try:
            self.db.add_customer_contact(self.customer["id"], email, name)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self.contact_email_input.clear()
        self.contact_name_input.clear()
        self._load_contacts()

    def _on_edit_contact(self, contact_id, contact):
        email, ok = QInputDialog.getText(
            self, "Edit email", "Email:", text=contact.get("email") or ""
        )
        if not ok or not email.strip():
            return
        name, ok2 = QInputDialog.getText(
            self, "Edit contact name", "Name (optional):", text=contact.get("name") or ""
        )
        if not ok2:
            return
        try:
            self.db.update_customer_contact(contact_id, email.strip(), name.strip())
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self._load_contacts()

    def _on_delete_contact(self, contact_id):
        if QMessageBox.question(self, "Remove email", "Remove this email contact?") != QMessageBox.Yes:
            return
        self.db.delete_customer_contact(contact_id)
        self._load_contacts()

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Account name is required.")
            return
        existing = self.db.get_customer_by_name(name)
        if existing and existing["id"] != self.customer["id"]:
            QMessageBox.warning(self, "Duplicate", f"Account '{name}' already exists.")
            return
        if name != self.customer.get("name"):
            self.db.update_customer(self.customer["id"], name)
        self.accept()
