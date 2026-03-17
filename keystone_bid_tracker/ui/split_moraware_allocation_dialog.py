from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QAbstractItemView,
    QApplication,
)

from config import get_config


class SplitMorawareAllocationDialog(QDialog):
    """Edit per-linked-job allocation totals for one bid."""

    def __init__(self, db, bid_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.bid_id = bid_id
        self.bid = self.db.get_bid_by_id(bid_id) or {}
        self.target = self.db.get_bid_allocation_target_totals(bid_id)
        self.setWindowTitle("Split Bid Allocation Across Moraware Jobs")
        self.resize(980, 520)
        self.setModal(True)
        self.did_split = False
        self._build_ui()
        self._load_rows()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel(f"{self.bid.get('bid_name') or 'Bid'}")
        title.setObjectName("headingLabel")
        root.addWidget(title)

        self.target_label = QLabel()
        self.target_label.setObjectName("secondaryLabel")
        root.addWidget(self.target_label)
        self.prefill_status_label = QLabel("")
        self.prefill_status_label.setObjectName("secondaryLabel")
        root.addWidget(self.prefill_status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Moraware Job ID",
                "Job #",
                "Ref TP",
                "Ref Sq Ft",
                "Alloc Bid Total",
                "Alloc Solid SF",
                "Alloc Stone SF",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.itemChanged.connect(self._on_item_changed)
        root.addWidget(self.table, 1)

        self.summary_label = QLabel("")
        self.summary_label.setObjectName("secondaryLabel")
        root.addWidget(self.summary_label)

        btn_row = QHBoxLayout()
        self.prefill_live_btn = QPushButton("Use Live Moraware Data")
        self.prefill_live_btn.clicked.connect(self._on_prefill_live_moraware)
        btn_row.addWidget(self.prefill_live_btn)
        self.prefill_synced_btn = QPushButton("Use Synced Moraware Data")
        self.prefill_synced_btn.clicked.connect(self._on_prefill_synced_moraware)
        btn_row.addWidget(self.prefill_synced_btn)
        btn_row.addStretch()
        self.split_btn = QPushButton("Split Bid from Moraware Jobs")
        self.split_btn.clicked.connect(self._on_split_bid)
        btn_row.addWidget(self.split_btn)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        self.save_btn = QPushButton("Save Allocation")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

    @staticmethod
    def _to_float(val):
        text = str(val if val is not None else "").strip().replace(",", "").replace("$", "")
        if not text:
            return 0.0
        try:
            return float(text)
        except Exception:
            return 0.0

    def _load_rows(self):
        rows = self.db.get_bid_moraware_allocations(self.bid_id)
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem((r.get("moraware_job_id") or "").strip()))
            self.table.setItem(i, 1, QTableWidgetItem((r.get("moraware_job_number") or "").strip()))

            ref_tp = float(r.get("reference_tp_total") or 0)
            ref_sf = float(r.get("reference_sq_ft_total") or 0)
            ref_tp_item = QTableWidgetItem(f"{ref_tp:,.2f}")
            ref_tp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, ref_tp_item)
            ref_sf_item = QTableWidgetItem(f"{ref_sf:,.2f}")
            ref_sf_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 3, ref_sf_item)

            alloc_bid_item = QTableWidgetItem(f"{float(r.get('allocated_bid_total') or 0):,.2f}")
            alloc_bid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 4, alloc_bid_item)
            alloc_ss_item = QTableWidgetItem(f"{float(r.get('allocated_solid_surf_sf') or 0):,.2f}")
            alloc_ss_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 5, alloc_ss_item)
            alloc_st_item = QTableWidgetItem(f"{float(r.get('allocated_stone_sf') or 0):,.2f}")
            alloc_st_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 6, alloc_st_item)
            self.table.setRowHeight(i, 34)

            for col in (0, 1, 2, 3):
                item = self.table.item(i, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.blockSignals(False)
        self._refresh_summary()

    def _allocation_rows(self):
        rows = []
        for i in range(self.table.rowCount()):
            jid = (self.table.item(i, 0).text() if self.table.item(i, 0) else "").strip()
            if not jid:
                continue
            rows.append(
                {
                    "moraware_job_id": jid,
                    "allocated_bid_total": self._to_float(self.table.item(i, 4).text() if self.table.item(i, 4) else "0"),
                    "allocated_solid_surf_sf": self._to_float(self.table.item(i, 5).text() if self.table.item(i, 5) else "0"),
                    "allocated_stone_sf": self._to_float(self.table.item(i, 6).text() if self.table.item(i, 6) else "0"),
                }
            )
        return rows

    def _refresh_summary(self):
        check = self.db.validate_bid_allocation_totals(self.bid_id, self._allocation_rows())
        expected = check["expected"]
        actual = check["actual"]
        delta = check["delta"]
        self.target_label.setText(
            "Target totals - "
            f"Bid Total: ${expected['bid_total']:,.2f} | "
            f"Solid SF: {expected['solid_surf_sf']:,.2f} | "
            f"Stone SF: {expected['stone_sf']:,.2f}"
        )
        self.summary_label.setText(
            "Current allocation - "
            f"Bid Total: ${actual['bid_total']:,.2f} (delta {delta['bid_total']:+.2f}) | "
            f"Solid SF: {actual['solid_surf_sf']:,.2f} (delta {delta['solid_surf_sf']:+.2f}) | "
            f"Stone SF: {actual['stone_sf']:,.2f} (delta {delta['stone_sf']:+.2f})"
        )
        if check["is_valid"]:
            self.summary_label.setStyleSheet("color: #9ccc65;")
        else:
            self.summary_label.setStyleSheet("color: #ef5350;")
        self.save_btn.setEnabled(check["is_valid"])

    def _on_item_changed(self, _item):
        self._refresh_summary()

    def _prefill_from_current_references(self):
        # Prefill proportionally from currently displayed reference TP/SF values.
        rows = []
        for i in range(self.table.rowCount()):
            jid = (self.table.item(i, 0).text() if self.table.item(i, 0) else "").strip()
            ref_tp = self._to_float(self.table.item(i, 2).text() if self.table.item(i, 2) else "0")
            ref_sf = self._to_float(self.table.item(i, 3).text() if self.table.item(i, 3) else "0")
            rows.append({"row": i, "jid": jid, "ref_tp": ref_tp, "ref_sf": ref_sf})

        if not rows:
            return

        target_bid = float(self.target.get("bid_total") or 0)
        target_ss = float(self.target.get("solid_surf_sf") or 0)
        target_st = float(self.target.get("stone_sf") or 0)
        target_total_sf = target_ss + target_st

        total_ref_tp = sum(r["ref_tp"] for r in rows)
        total_ref_sf = sum(r["ref_sf"] for r in rows)
        sf_split_ratio = (target_ss / target_total_sf) if target_total_sf > 0 else 0.0

        self.table.blockSignals(True)
        for r in rows:
            tp_share = (r["ref_tp"] / total_ref_tp) if total_ref_tp > 0 else (1.0 / len(rows))
            sf_share = (r["ref_sf"] / total_ref_sf) if total_ref_sf > 0 else (1.0 / len(rows))
            alloc_bid = target_bid * tp_share
            alloc_total_sf = target_total_sf * sf_share
            alloc_ss = alloc_total_sf * sf_split_ratio
            alloc_st = alloc_total_sf - alloc_ss

            self.table.setItem(r["row"], 4, QTableWidgetItem(f"{alloc_bid:,.2f}"))
            self.table.setItem(r["row"], 5, QTableWidgetItem(f"{alloc_ss:,.2f}"))
            self.table.setItem(r["row"], 6, QTableWidgetItem(f"{alloc_st:,.2f}"))

        # Force exact totals on the last row to avoid rounding drift.
        if rows:
            last = rows[-1]["row"]
            sum_bid = sum(self._to_float(self.table.item(i, 4).text()) for i in range(self.table.rowCount() - 1))
            sum_ss = sum(self._to_float(self.table.item(i, 5).text()) for i in range(self.table.rowCount() - 1))
            sum_st = sum(self._to_float(self.table.item(i, 6).text()) for i in range(self.table.rowCount() - 1))
            self.table.setItem(last, 4, QTableWidgetItem(f"{(target_bid - sum_bid):,.2f}"))
            self.table.setItem(last, 5, QTableWidgetItem(f"{(target_ss - sum_ss):,.2f}"))
            self.table.setItem(last, 6, QTableWidgetItem(f"{(target_st - sum_st):,.2f}"))

        for i in range(self.table.rowCount()):
            for col in (4, 5, 6):
                item = self.table.item(i, col)
                if item:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.blockSignals(False)
        self._refresh_summary()

    def _on_prefill_synced_moraware(self):
        self.prefill_status_label.setText("Prefill source: synced local Moraware invoice data.")
        self._prefill_from_current_references()

    def _set_prefill_buttons_enabled(self, enabled: bool):
        self.prefill_live_btn.setEnabled(enabled)
        self.prefill_synced_btn.setEnabled(enabled)
        self.split_btn.setEnabled(enabled)
        if not enabled:
            self.save_btn.setEnabled(False)

    def _on_prefill_live_moraware(self):
        cfg = get_config()
        username = (cfg.get("moraware_username") or "").strip()
        password = (cfg.get("moraware_password") or "").strip()
        base_url = (cfg.get("moraware_url") or "").strip()
        if not all([username, password, base_url]):
            QMessageBox.warning(self, "Moraware Not Configured", "Configure Moraware credentials in Settings.")
            return

        job_ids = []
        for i in range(self.table.rowCount()):
            jid = (self.table.item(i, 0).text() if self.table.item(i, 0) else "").strip()
            if jid and jid not in job_ids:
                job_ids.append(jid)
        if not job_ids:
            return

        existing_refs = {}
        for i in range(self.table.rowCount()):
            jid = (self.table.item(i, 0).text() if self.table.item(i, 0) else "").strip()
            if not jid:
                continue
            existing_refs[jid] = {
                "reference_tp_total": self._to_float(self.table.item(i, 2).text() if self.table.item(i, 2) else "0"),
                "reference_sq_ft_total": self._to_float(self.table.item(i, 3).text() if self.table.item(i, 3) else "0"),
            }

        self._set_prefill_buttons_enabled(False)
        self.prefill_status_label.setText("Fetching live Moraware reference totals...")
        QApplication.processEvents()
        try:
            from utils.moraware_client import MorewareClient
            client = MorewareClient(username, password, base_url, use_fast_sync=True)
            client.login()
            live_refs = client.get_live_reference_totals(job_ids)
        except Exception as e:
            self._set_prefill_buttons_enabled(True)
            QMessageBox.warning(self, "Live Fetch Failed", str(e))
            self.prefill_status_label.setText("Live fetch failed. You can still use synced data.")
            self._refresh_summary()
            return

        live_hits = 0
        fallback_hits = 0
        zero_hits = 0
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            jid = (self.table.item(i, 0).text() if self.table.item(i, 0) else "").strip()
            if not jid:
                continue
            live = live_refs.get(jid) or {}
            live_tp = float(live.get("reference_tp_total") or 0)
            live_sf = float(live.get("reference_sq_ft_total") or 0)
            local = existing_refs.get(jid) or {"reference_tp_total": 0.0, "reference_sq_ft_total": 0.0}
            local_tp = float(local.get("reference_tp_total") or 0)
            local_sf = float(local.get("reference_sq_ft_total") or 0)

            if live_tp > 0 or live_sf > 0:
                ref_tp = live_tp
                ref_sf = live_sf
                live_hits += 1
            elif local_tp > 0 or local_sf > 0:
                ref_tp = local_tp
                ref_sf = local_sf
                fallback_hits += 1
            else:
                ref_tp = 0.0
                ref_sf = 0.0
                zero_hits += 1

            self.table.setItem(i, 2, QTableWidgetItem(f"{ref_tp:,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{ref_sf:,.2f}"))

            live_job_num = (live.get("job_number") or "").strip()
            if live_job_num:
                existing_job_num = (self.table.item(i, 1).text() if self.table.item(i, 1) else "").strip()
                if not existing_job_num:
                    self.table.setItem(i, 1, QTableWidgetItem(live_job_num))

            for col in (2, 3):
                item = self.table.item(i, col)
                if item:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.blockSignals(False)
        self._set_prefill_buttons_enabled(True)

        self.prefill_status_label.setText(
            f"Live prefill refs: {live_hits} live, {fallback_hits} synced fallback, {zero_hits} no data."
        )
        self._prefill_from_current_references()

    def _on_save(self):
        rows = self._allocation_rows()
        try:
            self.db.save_bid_moraware_allocations(self.bid_id, rows)
        except ValueError as e:
            QMessageBox.warning(self, "Allocation Mismatch", str(e))
            self._refresh_summary()
            return
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return
        self.accept()

    def _on_split_bid(self):
        rows = self._allocation_rows()
        try:
            self.db.save_bid_moraware_allocations(self.bid_id, rows)
            self.db.split_bid_from_moraware_jobs(self.bid_id)
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Split Bid", str(e))
            self._refresh_summary()
            return
        except Exception as e:
            QMessageBox.critical(self, "Split Error", str(e))
            return
        self.did_split = True
        self.accept()
