from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QInputDialog,
)

from config import get_config


class LinkReviewDialog(QDialog):
    """Required link review gate before committing Moraware link."""

    def __init__(self, db, bid: dict, job: dict, moraware_client=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.bid = bid or {}
        self.job = job or {}
        self.moraware_client = moraware_client
        self.selected_customer_id = None
        self.selected_customer_name = ""
        self.result_payload = None
        self._tp_total = None
        self._sq_ft_total = None
        self._build_ui()
        self._load_live_refs()

    def _build_ui(self):
        self.setWindowTitle("Review Bid/Job Link")
        self.setMinimumSize(760, 420)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        title = QLabel("Required Review Before Linking")
        title.setObjectName("headingLabel")
        root.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)

        left_card = QFrame()
        left_card.setObjectName("card")
        left = QVBoxLayout(left_card)
        left.setContentsMargins(14, 12, 14, 12)
        left.setSpacing(8)
        left_title = QLabel("Bid Information")
        left_title.setObjectName("subheadingLabel")
        left.addWidget(left_title)
        left_divider = QFrame()
        left_divider.setFrameShape(QFrame.HLine)
        left_divider.setStyleSheet("border: none; background-color: #4a9eff; min-height: 1px; max-height: 1px;")
        left.addWidget(left_divider)
        left.addWidget(QLabel(self._format_line("Bid", self.bid.get("bid_name") or "")))
        left.addWidget(QLabel(self._format_line("Bid Total", f"${float(self.bid.get('bid_total') or 0):,.2f}")))
        left.addWidget(QLabel(self._format_line("Bid Solid SF", f"{float(self.bid.get('solid_surf_sf') or 0):,.0f}")))
        left.addWidget(QLabel(self._format_line("Bid Stone SF", f"{float(self.bid.get('stone_sf') or 0):,.0f}")))
        left.addWidget(QLabel(self._format_line("Bid Accounts", self.bid.get("customer_names") or "—")))
        left.addStretch()
        row.addWidget(left_card, 1)

        right_card = QFrame()
        right_card.setObjectName("card")
        right = QVBoxLayout(right_card)
        right.setContentsMargins(14, 12, 14, 12)
        right.setSpacing(8)
        right_title = QLabel("Moraware Job Information")
        right_title.setObjectName("subheadingLabel")
        right.addWidget(right_title)
        right_divider = QFrame()
        right_divider.setFrameShape(QFrame.HLine)
        right_divider.setStyleSheet("border: none; background-color: #4a9eff; min-height: 1px; max-height: 1px;")
        right.addWidget(right_divider)
        right.addWidget(QLabel(self._format_line("Moraware Job", self.job.get("name") or "")))
        right.addWidget(QLabel(self._format_line("Job #", (self.job.get("job_number") or self.job.get("id") or ""))))
        right.addWidget(QLabel(self._format_line("Moraware Account", self.job.get("account") or "—")))
        self.tp_label = QLabel(self._format_line("Moraware TP", "Loading..."))
        self.sf_label = QLabel(self._format_line("Moraware Sq Ft", "Loading..."))
        self.delta_label = QLabel(self._format_line("Delta", "Loading...", value_color="#f0f0f0"))
        right.addWidget(self.tp_label)
        right.addWidget(self.sf_label)
        right.addWidget(self.delta_label)
        right.addStretch()
        row.addWidget(right_card, 1)

        root.addLayout(row)

        cust_row = QHBoxLayout()
        cust_row.addWidget(QLabel("Winning account:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(320)
        for c in self.db.get_bid_customers(self.bid.get("id")):
            self.customer_combo.addItem(c["name"], c["id"])
        current_won = self.bid.get("won_customer_id")
        if current_won:
            idx = self.customer_combo.findData(current_won)
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)
        cust_row.addWidget(self.customer_combo, 1)
        add_btn = QPushButton("+ Add Account")
        add_btn.clicked.connect(self._on_add_customer)
        cust_row.addWidget(add_btn)
        root.addLayout(cust_row)

        self.mismatch_label = QLabel("")
        self.mismatch_label.setObjectName("secondaryLabel")
        self.mismatch_label.setWordWrap(True)
        root.addWidget(self.mismatch_label)
        self._refresh_mismatch_text()
        self.customer_combo.currentIndexChanged.connect(self._refresh_mismatch_text)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        confirm_btn = QPushButton("Confirm Link")
        confirm_btn.setObjectName("primaryButton")
        confirm_btn.clicked.connect(self._on_confirm)
        btns.addWidget(confirm_btn)
        root.addLayout(btns)

    def _format_line(self, label: str, value: str, value_color: str = "#d0d0d0") -> str:
        safe_value = str(value) if value is not None else ""
        return (
            f"<span style='font-weight: 600; color: #f0f0f0;'>{label}:</span> "
            f"<span style='color: {value_color};'>{safe_value}</span>"
        )

    def _load_live_refs(self):
        job_id = str(self.job.get("id") or "").strip()
        if not job_id:
            self.tp_label.setText(self._format_line("Moraware TP", "—"))
            self.sf_label.setText(self._format_line("Moraware Sq Ft", "—"))
            self.delta_label.setText(self._format_line("Delta", "unavailable", value_color="#b0b0b0"))
            return
        client = self.moraware_client
        if client is None:
            cfg = get_config()
            username = (cfg.get("moraware_username") or "").strip()
            password = (cfg.get("moraware_password") or "").strip()
            base_url = (cfg.get("moraware_url") or "").strip()
            if not all([username, password, base_url]):
                self.tp_label.setText(self._format_line("Moraware TP", "(credentials missing)", value_color="#b0b0b0"))
                self.sf_label.setText(self._format_line("Moraware Sq Ft", "(credentials missing)", value_color="#b0b0b0"))
                self.delta_label.setText(self._format_line("Delta", "unavailable", value_color="#b0b0b0"))
                return
            try:
                from utils.moraware_client import MorewareClient
                client = MorewareClient(username, password, base_url, use_fast_sync=True)
                client.login()
            except Exception as e:
                self.tp_label.setText(self._format_line("Moraware TP", f"fetch failed ({e})", value_color="#d9534f"))
                self.sf_label.setText(self._format_line("Moraware Sq Ft", "fetch failed", value_color="#d9534f"))
                self.delta_label.setText(self._format_line("Delta", "unavailable", value_color="#b0b0b0"))
                return
        try:
            refs = client.get_live_reference_totals([job_id])
            payload = refs.get(job_id) or {}
            self._tp_total = float(payload.get("reference_tp_total") or 0)
            self._sq_ft_total = float(payload.get("reference_sq_ft_total") or 0)
        except Exception:
            self._tp_total = None
            self._sq_ft_total = None

        if self._tp_total is None:
            self.tp_label.setText(self._format_line("Moraware TP", "—"))
            self.sf_label.setText(self._format_line("Moraware Sq Ft", "—"))
            self.delta_label.setText(self._format_line("Delta", "unavailable", value_color="#b0b0b0"))
            return

        bid_total = float(self.bid.get("bid_total") or 0)
        bid_sf = float(self.bid.get("solid_surf_sf") or 0) + float(self.bid.get("stone_sf") or 0)
        tp_delta = self._tp_total - bid_total
        sf_delta = self._sq_ft_total - bid_sf
        delta_color = "#8fd18f" if abs(tp_delta) < 0.01 and abs(sf_delta) < 0.01 else "#f0c674"
        self.tp_label.setText(self._format_line("Moraware TP", f"${self._tp_total:,.2f}"))
        self.sf_label.setText(self._format_line("Moraware Sq Ft", f"{self._sq_ft_total:,.0f}"))
        self.delta_label.setText(self._format_line("Delta", f"${tp_delta:+,.2f} | SF {sf_delta:+,.0f}", value_color=delta_color))

    def _refresh_mismatch_text(self):
        mw_account = (self.job.get("account") or "").strip()
        local = (self.customer_combo.currentText() or "").strip()
        if mw_account and local and mw_account.lower() != local.lower():
            self.mismatch_label.setText(
                f"Account mismatch: local '{local}' vs Moraware '{mw_account}'. "
                "You can keep local or switch to Moraware on confirm."
            )
        else:
            self.mismatch_label.setText("")

    def _on_add_customer(self):
        name, ok = QInputDialog.getText(self, "Add Account", "Account name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        existing = self.db.get_customer_by_name(name)
        if existing:
            cust_id = int(existing["id"])
        else:
            cust_id = int(self.db.add_customer(name))
        bid_id = int(self.bid.get("id") or 0)
        if bid_id:
            with self.db._conn() as conn:
                link = conn.execute(
                    "SELECT 1 FROM bid_customers WHERE bid_id=? AND customer_id=? LIMIT 1",
                    (bid_id, cust_id),
                ).fetchone()
                if not link:
                    conn.execute(
                        "INSERT INTO bid_customers (bid_id, customer_id) VALUES (?, ?)",
                        (bid_id, cust_id),
                    )
        idx = self.customer_combo.findData(cust_id)
        if idx < 0:
            self.customer_combo.addItem(name, cust_id)
            idx = self.customer_combo.findData(cust_id)
        if idx >= 0:
            self.customer_combo.setCurrentIndex(idx)

    def _resolve_moraware_account_choice(self) -> bool:
        mw_account = (self.job.get("account") or "").strip()
        if not mw_account:
            return True
        local_name = (self.customer_combo.currentText() or "").strip()
        if not local_name or local_name.lower() == mw_account.lower():
            return True

        msg = QMessageBox(self)
        msg.setWindowTitle("Account Mismatch")
        msg.setText(
            f"Winning account differs from Moraware account.\n\n"
            f"Local: {local_name}\nMoraware: {mw_account}\n\n"
            "Use Moraware account instead?"
        )
        use_mw = msg.addButton("Use Moraware Account", QMessageBox.AcceptRole)
        keep_local = msg.addButton("Keep Local Account", QMessageBox.DestructiveRole)
        cancel = msg.addButton(QMessageBox.Cancel)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked == cancel:
            return False
        if clicked == keep_local:
            return True

        existing = self.db.get_customer_by_name(mw_account)
        if existing:
            cust_id = int(existing["id"])
        else:
            create = QMessageBox.question(
                self,
                "Add Moraware Account",
                f"Moraware account '{mw_account}' does not exist locally.\nAdd it now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if create != QMessageBox.Yes:
                return False
            cust_id = int(self.db.add_customer(mw_account))
        bid_id = int(self.bid.get("id") or 0)
        if bid_id:
            with self.db._conn() as conn:
                link = conn.execute(
                    "SELECT 1 FROM bid_customers WHERE bid_id=? AND customer_id=? LIMIT 1",
                    (bid_id, cust_id),
                ).fetchone()
                if not link:
                    conn.execute(
                        "INSERT INTO bid_customers (bid_id, customer_id) VALUES (?, ?)",
                        (bid_id, cust_id),
                    )
        idx = self.customer_combo.findData(cust_id)
        if idx < 0:
            self.customer_combo.addItem(mw_account, cust_id)
            idx = self.customer_combo.findData(cust_id)
        if idx >= 0:
            self.customer_combo.setCurrentIndex(idx)
        return True

    def _on_confirm(self):
        if self.customer_combo.count() <= 0:
            QMessageBox.warning(self, "Missing Account", "Add or select a winning account.")
            return
        if not self._resolve_moraware_account_choice():
            return
        self.selected_customer_id = int(self.customer_combo.currentData())
        self.selected_customer_name = (self.customer_combo.currentText() or "").strip()
        self.result_payload = {
            "won_customer_id": self.selected_customer_id,
            "won_customer_name": self.selected_customer_name,
            "tp_total": self._tp_total,
            "sq_ft_total": self._sq_ft_total,
            "confirmed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.accept()
