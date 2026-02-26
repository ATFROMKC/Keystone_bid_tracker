"""
Keystone Bid Tracker - Add Revision Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QPushButton, QLabel, QHBoxLayout, QMessageBox,
)
from PyQt5.QtCore import Qt, QDate


class AddRevisionDialog(QDialog):
    def __init__(self, db, bid_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.bid_id = bid_id
        self.result_data = None

        bid = self.db.get_bid_by_id(bid_id)
        latest = self.db.get_latest_revision(bid_id)
        self.next_rev = (latest["revision_no"] + 1) if latest else 1

        self.setWindowTitle("Add Revision")
        self.setMinimumSize(420, 380)
        self.setModal(True)

        self._build_ui(bid, latest)

    def _build_ui(self, bid, latest):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Add Revision")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        bid_label = QLabel(bid["bid_name"])
        bid_label.setObjectName("subheadingLabel")
        layout.addWidget(bid_label)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        rev_label = QLabel(f"Rev #{self.next_rev}")
        rev_label.setStyleSheet("font-weight: 600; color: #4a9eff;")
        form.addRow("Revision #", rev_label)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Revision Date *", self.date_input)

        self.total_input = QLineEdit()
        self.total_input.setPlaceholderText("0.00")
        if latest and latest["bid_total"]:
            self.total_input.setText(str(latest["bid_total"]))
        form.addRow("New Bid Total ($) *", self.total_input)

        self.solid_sf_input = QLineEdit()
        self.solid_sf_input.setPlaceholderText("0")
        if latest and latest["solid_surf_sf"]:
            self.solid_sf_input.setText(str(latest["solid_surf_sf"]))
        form.addRow("Solid Surface SF", self.solid_sf_input)

        self.stone_sf_input = QLineEdit()
        self.stone_sf_input.setPlaceholderText("0")
        if latest and latest["stone_sf"]:
            self.stone_sf_input.setText(str(latest["stone_sf"]))
        form.addRow("Stone SF", self.stone_sf_input)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Reason for revision (optional)")
        form.addRow("Reason", self.reason_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Revision")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _on_save(self):
        total_text = self.total_input.text().strip().replace(",", "").replace("$", "")
        solid_text = self.solid_sf_input.text().strip().replace(",", "")
        stone_text = self.stone_sf_input.text().strip().replace(",", "")

        errors = []
        try:
            bid_total = float(total_text) if total_text else 0.0
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

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        self.result_data = {
            "revision_date": self.date_input.date().toString("yyyy-MM-dd"),
            "bid_total": bid_total,
            "solid_surf_sf": solid_sf,
            "stone_sf": stone_sf,
            "reason": self.reason_input.text().strip(),
        }
        self.accept()
