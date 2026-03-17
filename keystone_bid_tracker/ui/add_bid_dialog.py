"""
Keystone Bid Tracker - Add / Edit Bid Dialog
Modal form with customer multi-select, validation, and inline customer creation.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QTextEdit, QPushButton, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QWidget, QAbstractItemView, QComboBox,
)
from PyQt5.QtCore import Qt, QDate


class AddBidDialog(QDialog):
    """Dialog for adding or editing a bid."""

    def __init__(self, db, parent=None, bid_data=None):
        super().__init__(parent)
        self.db = db
        self.bid_data = bid_data
        self.result_data = None

        editing = bid_data is not None
        self.setWindowTitle("Edit Bid" if editing else "Add New Bid")
        self.setMinimumSize(560, 640)
        self.setModal(True)

        self._build_ui()
        if editing:
            self._populate(bid_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Edit Bid" if self.bid_data else "Add New Bid")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter bid name...")
        form.addRow("Bid Name *", self.name_input)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Bid Date *", self.date_input)

        self.estimator_input = QComboBox()
        self.estimator_input.setEditable(True)
        self.estimator_input.setInsertPolicy(QComboBox.NoInsert)
        self.estimator_input.lineEdit().setPlaceholderText("Estimator name...")
        self._load_estimators()
        form.addRow("Estimator *", self.estimator_input)

        self.total_input = QLineEdit()
        self.total_input.setPlaceholderText("0.00")
        form.addRow("Bid Total ($) *", self.total_input)

        self.solid_sf_input = QLineEdit()
        self.solid_sf_input.setPlaceholderText("0")
        form.addRow("Solid Surface SF", self.solid_sf_input)

        self.stone_sf_input = QLineEdit()
        self.stone_sf_input.setPlaceholderText("0")
        form.addRow("Stone SF", self.stone_sf_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional notes...")
        self.notes_input.setMaximumHeight(80)
        form.addRow("Notes", self.notes_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["PENDING", "BIDDING", "WON"])
        if self.bid_data:
            form.addRow("Status", self.status_combo)
        else:
            self.status_combo.hide()

        layout.addLayout(form)

        # Customer multi-select section
        cust_header = QHBoxLayout()
        cust_label = QLabel("Accounts * (select at least 1)")
        cust_label.setObjectName("subheadingLabel")
        cust_header.addWidget(cust_label)
        cust_header.addStretch()

        add_cust_btn = QPushButton("+ New Customer")
        add_cust_btn.setFixedHeight(28)
        add_cust_btn.clicked.connect(self._on_add_customer)
        cust_header.addWidget(add_cust_btn)
        layout.addLayout(cust_header)

        self.cust_search = QLineEdit()
        self.cust_search.setPlaceholderText("Search customers...")
        self.cust_search.textChanged.connect(self._filter_customers)
        layout.addWidget(self.cust_search)

        self.cust_list = QListWidget()
        self.cust_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.cust_list.setMinimumHeight(120)
        self.cust_list.setMaximumHeight(180)
        layout.addWidget(self.cust_list)

        self._load_customers()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Bid")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_customers(self, select_ids=None):
        self.cust_list.clear()
        customers = self.db.get_customers(active_only=True)

        # If editing, also include currently linked customers even if inactive
        if self.bid_data and select_ids:
            linked = self.db.get_bid_customers(self.bid_data["id"])
            linked_ids = {c["id"] for c in linked}
            existing_ids = {c["id"] for c in customers}
            for lc in linked:
                if lc["id"] not in existing_ids:
                    customers.append(lc)

        for c in customers:
            item = QListWidgetItem(c["name"])
            item.setData(Qt.UserRole, c["id"])
            item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if select_ids and c["id"] in select_ids else Qt.Unchecked)
            self.cust_list.addItem(item)

        self._filter_customers(self.cust_search.text().strip())

    def _filter_customers(self, text):
        for i in range(self.cust_list.count()):
            item = self.cust_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_add_customer(self):
        name, ok = QInputDialog.getText(self, "Add Account", "Account name:")
        if ok and name.strip():
            existing = self.db.get_customer_by_name(name.strip())
            if existing:
                QMessageBox.information(self, "Exists", f"'{name.strip()}' already exists. Selecting it.")
                for i in range(self.cust_list.count()):
                    item = self.cust_list.item(i)
                    if item.data(Qt.UserRole) == existing["id"]:
                        item.setCheckState(Qt.Checked)
                        break
                return
            cid = self.db.add_customer(name.strip())
            selected_ids = self._get_selected_customer_ids()
            selected_ids.add(cid)
            self._load_customers(select_ids=selected_ids)

    def _get_selected_customer_ids(self):
        ids = set()
        for i in range(self.cust_list.count()):
            item = self.cust_list.item(i)
            if item.checkState() == Qt.Checked:
                ids.add(item.data(Qt.UserRole))
        return ids

    def _load_estimators(self):
        self.estimator_input.clear()
        for estimator in self.db.get_estimators():
            if estimator:
                self.estimator_input.addItem(estimator)

    def _populate(self, data):
        self.name_input.setText(data.get("bid_name", ""))
        if data.get("original_bid_date"):
            d = QDate.fromString(data["original_bid_date"], "yyyy-MM-dd")
            if d.isValid():
                self.date_input.setDate(d)
        estimator_name = data.get("estimator", "")
        idx = self.estimator_input.findText(estimator_name)
        if idx >= 0:
            self.estimator_input.setCurrentIndex(idx)
        else:
            self.estimator_input.setEditText(estimator_name)

        rev = self.db.get_latest_revision(data["id"])
        if rev:
            self.total_input.setText(str(rev["bid_total"]) if rev["bid_total"] else "")
            self.solid_sf_input.setText(str(rev["solid_surf_sf"]) if rev["solid_surf_sf"] else "")
            self.stone_sf_input.setText(str(rev["stone_sf"]) if rev["stone_sf"] else "")

        self.notes_input.setPlainText(data.get("notes", "") or "")

        current_status = data.get("status", "PENDING")
        idx = self.status_combo.findText(current_status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        linked = self.db.get_bid_customers(data["id"])
        linked_ids = {c["id"] for c in linked}
        self._load_customers(select_ids=linked_ids)

    def _on_save(self):
        bid_name = self.name_input.text().strip()
        estimator = self.estimator_input.currentText().strip()
        total_text = self.total_input.text().strip().replace(",", "").replace("$", "")
        solid_text = self.solid_sf_input.text().strip().replace(",", "")
        stone_text = self.stone_sf_input.text().strip().replace(",", "")
        notes = self.notes_input.toPlainText().strip()
        selected_ids = list(self._get_selected_customer_ids())

        errors = []
        if not bid_name:
            errors.append("Bid Name is required.")
        if not estimator:
            errors.append("Estimator is required.")
        try:
            bid_total = float(total_text) if total_text else 0.0
            if bid_total < 0:
                errors.append("Bid Total must be >= 0.")
        except ValueError:
            errors.append("Bid Total must be a valid number.")
            bid_total = 0

        try:
            solid_sf = float(solid_text) if solid_text else 0.0
        except ValueError:
            errors.append("Solid Surface SF must be a valid number.")
            solid_sf = 0

        try:
            stone_sf = float(stone_text) if stone_text else 0.0
        except ValueError:
            errors.append("Stone SF must be a valid number.")
            stone_sf = 0

        if not selected_ids:
            errors.append("Select at least one customer.")

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        bid_date = self.date_input.date().toString("yyyy-MM-dd")

        self.result_data = {
            "bid_name": bid_name,
            "estimator": estimator,
            "original_bid_date": bid_date,
            "bid_total": bid_total,
            "solid_surf_sf": solid_sf,
            "stone_sf": stone_sf,
            "notes": notes,
            "customer_ids": selected_ids,
            "status": self.status_combo.currentText(),
        }
        self.accept()
