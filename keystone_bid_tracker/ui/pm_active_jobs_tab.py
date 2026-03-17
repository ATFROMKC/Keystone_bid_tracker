"""
Keystone Bid Tracker - PM Active Jobs Tab
Moraware-driven active jobs with local bid link overlay and PM workflow actions.
"""

import os
import re
import webbrowser
from datetime import datetime
from urllib.parse import urlparse

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QInputDialog,
)

from config import get_config
from ui.awarded_tab import AwardedDetailPanel, InvoiceSyncWorker, PMEditJobDialog
from ui.link_local_bid_dialog import LinkLocalBidDialog
from ui.link_review_dialog import LinkReviewDialog
from ui.split_moraware_allocation_dialog import SplitMorawareAllocationDialog


def _norm_text(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


class _FetchActiveJobsWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            from utils.moraware_client import MorewareClient

            cfg = get_config()
            username = (cfg.get("moraware_username") or "").strip()
            password = (cfg.get("moraware_password") or "").strip()
            base_url = (cfg.get("moraware_url") or "").strip()
            if not all([username, password, base_url]):
                raise RuntimeError("Moraware credentials are not configured in Settings.")

            client = MorewareClient(username, password, base_url)
            client.login()
            jobs = client.list_jobs(active_only=True, pagesize=300, max_pages=30)
            self.finished.emit(jobs)
        except Exception as exc:
            self.error.emit(str(exc))


class PMActiveJobsTab(QWidget):
    def __init__(self, db, session_cache: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.session_cache = session_cache or {}
        self._jobs_cache = []
        self._display_rows = []
        self._worker = None
        self._sync_worker = None
        self._selected_bid_id = None
        self._build_ui()
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("Active Jobs")
        title.setObjectName("headingLabel")
        root.addWidget(title)
        sub = QLabel("Moraware active jobs with local bid link status")
        sub.setObjectName("secondaryLabel")
        root.addWidget(sub)

        filt = QHBoxLayout()
        filt.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search jobs...")
        self.search_input.setMaximumWidth(280)
        self.search_input.textChanged.connect(self._render_rows)
        filt.addWidget(self.search_input)

        self.pm_combo = QComboBox()
        self.pm_combo.setMinimumWidth(180)
        self.pm_combo.currentIndexChanged.connect(self._render_rows)
        filt.addWidget(self.pm_combo)

        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(170)
        self.status_combo.addItems(
            [
                "All Included",
                "Active",
                "Unscheduled",
                "30+ Days Old",
            ]
        )
        self.status_combo.currentIndexChanged.connect(self._render_rows)
        filt.addWidget(self.status_combo)

        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        filt.addWidget(clear_btn)

        self.refresh_btn = QPushButton("Reload Job List")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.setToolTip("Reload the Moraware Active Jobs list.")
        self.refresh_btn.clicked.connect(lambda: self.refresh(force_fetch=True))
        filt.addWidget(self.refresh_btn)

        self.sync_all_btn = QPushButton("Refresh All Jobs")
        self.sync_all_btn.clicked.connect(self._sync_all_linked)
        filt.addWidget(self.sync_all_btn)

        filt.addStretch()

        self.showing_label = QLabel("")
        self.showing_label.setObjectName("secondaryLabel")
        filt.addWidget(self.showing_label)
        root.addLayout(filt)

        self.status_label = QLabel("")
        self.status_label.setObjectName("secondaryLabel")
        root.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "#",
                "MW Job #",
                "Job Name",
                "Account",
                "Salesperson",
                "PM",
                "Link Status",
                "Linked Bid",
                "Local Status",
                "Mismatch",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.clicked.connect(self._on_row_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.Stretch)
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

        self.unlinked_detail_label = QLabel("No local bid is linked to the selected Moraware job yet.")
        self.unlinked_detail_label.setObjectName("secondaryLabel")
        self.unlinked_detail_label.hide()
        root.addWidget(self.unlinked_detail_label)

        self.detail_panel = AwardedDetailPanel(self)
        self.detail_panel.action_triggered.connect(self._on_detail_action)
        self.detail_panel.refresh_btn.setText("Refresh Job")
        self.detail_panel.refresh_btn.setToolTip("Refresh this job from Moraware (metadata + invoices)")
        self.detail_panel.btn_refresh_inv.setText("Refresh Job")
        self.detail_panel.hide()
        root.addWidget(self.detail_panel)

    def refresh(self, force_fetch=False):
        cached = self.session_cache.get("jobs") or []
        if force_fetch:
            self._fetch_jobs()
            return
        if cached:
            self._jobs_cache = list(cached)
            self._rebuild_pm_filter()
            self._render_rows(update_status=True, status_prefix="Using session cache.")
            return
        self._fetch_jobs()

    def _fetch_jobs(self):
        if self._worker and self._worker.isRunning():
            return
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Reloading...")
        self.status_label.setText("Fetching active jobs from Moraware...")
        self._worker = _FetchActiveJobsWorker()
        self._worker.finished.connect(self._on_jobs_fetched)
        self._worker.error.connect(self._on_fetch_error)
        self._worker.start()

    def _on_jobs_fetched(self, jobs):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Reload Job List")
        self._jobs_cache = jobs or []
        self.session_cache["jobs"] = list(self._jobs_cache)
        self.session_cache["fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._rebuild_pm_filter()
        self._render_rows(update_status=True, status_prefix="Loaded Moraware jobs.")

    def _on_fetch_error(self, message):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Reload Job List")
        self._jobs_cache = list(self.session_cache.get("jobs") or [])
        self._rebuild_pm_filter()
        self._render_rows(
            update_status=True,
            status_prefix=f"Unable to load Moraware jobs ({message}). Using cache."
        )

    def _rebuild_pm_filter(self):
        current = self.pm_combo.currentText()

        canonical = {}
        for pm in self.db.get_project_managers() or []:
            norm = _norm_text(pm)
            if norm and norm not in canonical:
                canonical[norm] = pm.strip()
        for job in self._jobs_cache:
            pm = (job.get("project_manager") or "").strip()
            norm = _norm_text(pm)
            if norm and norm not in canonical:
                canonical[norm] = pm

        pm_values = [canonical[k] for k in sorted(canonical.keys())]

        self.pm_combo.blockSignals(True)
        self.pm_combo.clear()
        self.pm_combo.addItem("All Project Managers")
        for pm in pm_values:
            self.pm_combo.addItem(pm)
        idx = self.pm_combo.findText(current)
        self.pm_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.pm_combo.blockSignals(False)

    def _render_rows(self, update_status: bool = False, status_prefix: str = ""):
        jobs = list(self._jobs_cache)
        selected_pm = self.pm_combo.currentText().strip()
        selected_pm_norm = _norm_text(selected_pm)
        if selected_pm and selected_pm != "All Project Managers":
            jobs = [
                j for j in jobs
                if _norm_text(j.get("project_manager") or "") == selected_pm_norm
            ]

        job_ids = [str(j.get("id") or "").strip() for j in jobs if str(j.get("id") or "").strip()]
        all_link_map = self.db.get_all_bid_links_by_moraware_job_ids(job_ids)
        selected_status = self.status_combo.currentText().strip()
        if selected_status and selected_status != "All Included":
            selected_status_norm = _norm_text(selected_status)
            jobs = [
                j for j in jobs
                if _norm_text(j.get("status") or "") == selected_status_norm
            ]

        q = self.search_input.text().strip().lower()
        if q:
            jobs = [
                j
                for j in jobs
                if q in (j.get("name") or "").lower()
                or q in (j.get("job_number") or "").lower()
                or q in (j.get("account") or "").lower()
            ]

        rows = []
        for job in jobs:
            jid = str(job.get("id") or "").strip()
            linked_candidates = all_link_map.get(jid) or []
            primary_link = next(
                (x for x in linked_candidates if int((x or {}).get("is_primary") or 0) == 1),
                None,
            )
            linked = primary_link or (linked_candidates[0] if linked_candidates else None)
            if not linked_candidates:
                link_status = "Not Linked"
            elif len(linked_candidates) == 1:
                link_status = "Linked (Primary)" if int((linked or {}).get("is_primary") or 0) == 1 else "Linked (Secondary)"
            else:
                link_status = f"Linked ({len(linked_candidates)} bids)"
            rows.append(
                {
                    "job_id": jid,
                    "job": job,
                    "linked_bid": linked,
                    "link_status": link_status,
                    "local_status": (linked or {}).get("status") or "",
                    "mismatch": bool(linked and (linked or {}).get("status") != "WON"),
                    "moraware_status": (job.get("status") or "").strip(),
                }
            )
        self._display_rows = rows

        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            job = row["job"]
            linked = row["linked_bid"] or {}

            idx_item = QTableWidgetItem(str(row_idx + 1))
            idx_item.setTextAlignment(Qt.AlignCenter)
            idx_item.setData(Qt.UserRole, row["job_id"])
            idx_item.setData(Qt.UserRole + 1, linked.get("id"))
            self.table.setItem(row_idx, 0, idx_item)
            self.table.setItem(row_idx, 1, QTableWidgetItem(job.get("job_number") or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(job.get("name") or ""))
            self.table.setItem(row_idx, 3, QTableWidgetItem(job.get("account") or ""))
            self.table.setItem(row_idx, 4, QTableWidgetItem(job.get("salesperson") or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem(job.get("project_manager") or ""))
            self.table.setItem(row_idx, 6, QTableWidgetItem(row["link_status"]))
            self.table.setItem(row_idx, 7, QTableWidgetItem(linked.get("bid_name") or ""))
            self.table.setItem(row_idx, 8, QTableWidgetItem(row["local_status"]))
            self.table.setItem(row_idx, 9, QTableWidgetItem("Yes" if row["mismatch"] else ""))
            self.table.setRowHeight(row_idx, 38)

        pm_scope = selected_pm if selected_pm and selected_pm != "All Project Managers" else "All PMs"
        status_scope = selected_status or "All Included"
        self.showing_label.setText(
            f"{pm_scope} | {status_scope}: {len(rows)} jobs (of {len(self._jobs_cache)} total)"
        )
        if update_status:
            prefix = f"{status_prefix} " if status_prefix else ""
            self.status_label.setText(
                f"{prefix}Total fetched: {len(self._jobs_cache)} | "
                f"Visible after PM/Status/Search: {len(rows)}."
            )

        if not rows:
            self._selected_bid_id = None
            self.detail_panel.hide()
            self.unlinked_detail_label.hide()

    def _clear_filters(self):
        self.search_input.clear()
        self.pm_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self._render_rows()

    def _on_row_clicked(self, index):
        row_idx = index.row()
        if row_idx < 0 or row_idx >= len(self._display_rows):
            return
        self._show_detail_for_row(row_idx)

    def _show_detail_for_row(self, row_idx: int):
        row = self._display_rows[row_idx]
        linked_bid = row.get("linked_bid") or {}
        bid_id = linked_bid.get("id")
        if bid_id:
            self._selected_bid_id = bid_id
            self.unlinked_detail_label.hide()
            self.detail_panel.load_bid(self.db, bid_id)
            self.detail_panel.show()
        else:
            self._selected_bid_id = None
            self.detail_panel.hide()
            self.unlinked_detail_label.setText(
                "No local bid is linked to this Moraware job yet."
            )
            self.unlinked_detail_label.show()

    def _show_context_menu(self, pos):
        idx = self.table.indexAt(pos)
        row_idx = idx.row()
        if row_idx < 0 or row_idx >= len(self._display_rows):
            return

        row = self._display_rows[row_idx]
        job_id = row["job_id"]
        linked_bid = row.get("linked_bid") or {}
        bid_id = linked_bid.get("id")

        self.table.selectRow(row_idx)
        self._show_detail_for_row(row_idx)

        menu = QMenu(self)
        open_action = menu.addAction("Open in Moraware")
        link_action = menu.addAction("Link to Local Bid...")
        add_another_action = menu.addAction("Add Another Job to This Quote...")
        sync_action = menu.addAction("Refresh Job")
        split_action = menu.addAction("Split Bid from Moraware Jobs...")
        unsync_action = menu.addAction("Unsync from Moraware")
        edit_action = menu.addAction("Edit Job")
        move_back_action = menu.addAction("Move Back to Bidding")
        if not bid_id:
            add_another_action.setEnabled(False)
            sync_action.setEnabled(False)
            split_action.setEnabled(False)
            unsync_action.setEnabled(False)
            edit_action.setEnabled(False)
            move_back_action.setEnabled(False)
        else:
            link_count = len(self.db.get_bid_moraware_links(bid_id))
            bid = self.db.get_bid_by_id(bid_id) or {}
            if link_count < 2 or (str(bid.get("bid_role") or "normal").strip().lower() == "child"):
                split_action.setEnabled(False)
        chosen = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if chosen == open_action:
            self._open_in_moraware(job_id)
        elif chosen == link_action:
            self._link_to_local_bid(
                job_id,
                row.get("job", {}).get("job_number") or "",
                row.get("job", {}).get("name") or "",
                row.get("job", {}).get("account") or "",
                row.get("job", {}).get("salesperson") or "",
                row.get("job", {}).get("project_manager") or "",
            )
        elif chosen == add_another_action and bid_id:
            self._add_another_job_to_quote(bid_id, exclude_job_id=job_id)
        elif chosen == sync_action and bid_id:
            self._sync_single_bid(bid_id)
        elif chosen == split_action and bid_id:
            self._split_bid_from_moraware(bid_id)
        elif chosen == unsync_action and bid_id:
            self._unsync_from_moraware(bid_id)
        elif chosen == edit_action and bid_id:
            self._edit_job(bid_id)
        elif chosen == move_back_action and bid_id:
            self._move_back_to_bidding(bid_id)

    def _link_to_local_bid(
        self,
        job_id: str,
        job_number: str = "",
        job_name: str = "",
        job_account: str = "",
        moraware_salesperson: str = "",
        moraware_project_manager: str = "",
        target_bid_id: int = None,
    ):
        if target_bid_id:
            selected_bid = self.db.get_bid_by_id(int(target_bid_id)) or {}
            selected_bid_id = int(target_bid_id)
        else:
            picker = LinkLocalBidDialog(self.db, self)
            if not picker.exec_() or not picker.selected_bid:
                return
            selected_bid = picker.selected_bid
            selected_bid_id = selected_bid.get("id")
        if not selected_bid_id:
            return

        review_bid = next(
            (b for b in (self.db.get_linkable_bids(search="") or []) if int(b.get("id") or 0) == int(selected_bid_id)),
            None,
        ) or (self.db.get_bid_by_id(int(selected_bid_id)) or {})
        review_job = {
            "id": str(job_id or "").strip(),
            "job_number": (job_number or "").strip(),
            "name": (job_name or "").strip(),
            "account": (job_account or "").strip(),
            "salesperson": (moraware_salesperson or "").strip(),
            "project_manager": (moraware_project_manager or "").strip(),
        }
        review_dlg = LinkReviewDialog(self.db, review_bid, review_job, parent=self)
        if not review_dlg.exec_() or not review_dlg.selected_customer_id:
            return
        chosen_customer_id = int(review_dlg.selected_customer_id)
        bid_state = self.db.get_bid_by_id(int(selected_bid_id)) or {}
        if str((bid_state.get("status") or "")).strip().upper() == "WON":
            if int(bid_state.get("won_customer_id") or 0) != chosen_customer_id:
                self.db.update_won_details(
                    int(selected_bid_id),
                    chosen_customer_id,
                    salesperson=(bid_state.get("salesperson") or "").strip(),
                    project_manager=(bid_state.get("project_manager") or "").strip(),
                    moraware_job_date=bid_state.get("moraware_job_date"),
                    won_notes=(bid_state.get("won_notes") or "").strip(),
                    est_complete_date=bid_state.get("est_complete_date"),
                    est_complete_date_manual=bid_state.get("est_complete_date_manual"),
                    est_start_month=bid_state.get("est_start_month"),
                    won_date=bid_state.get("won_date"),
                )
        else:
            self.db.ensure_bid_won_for_link(
                int(selected_bid_id),
                won_customer_id=chosen_customer_id,
                salesperson=(moraware_salesperson or "").strip(),
                project_manager=(moraware_project_manager or "").strip(),
            )

        make_primary = True
        existing_for_bid = self.db.get_bid_moraware_links(selected_bid_id)
        already_linked = any(str((x or {}).get("moraware_job_id") or "").strip() == str(job_id).strip() for x in existing_for_bid)
        has_other_links = any(str((x or {}).get("moraware_job_id") or "").strip() != str(job_id).strip() for x in existing_for_bid)
        if already_linked:
            reply = QMessageBox.question(
                self,
                "Link Already Exists",
                "This bid already has this Moraware job linked.\n\nSet it as the primary link?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
            self.db.set_primary_bid_moraware_link(selected_bid_id, str(job_id).strip())
        elif has_other_links:
            msg = QMessageBox(self)
            msg.setWindowTitle("Bid Has Existing Links")
            msg.setText(
                f"'{selected_bid.get('bid_name') or 'Selected bid'}' already has Moraware link(s).\n\n"
                "Choose how to add this job link."
            )
            add_secondary = msg.addButton("Add as Secondary", QMessageBox.AcceptRole)
            set_primary = msg.addButton("Add + Set Primary", QMessageBox.DestructiveRole)
            msg.addButton(QMessageBox.Cancel)
            msg.exec_()
            clicked = msg.clickedButton()
            if clicked == add_secondary:
                make_primary = False
            elif clicked == set_primary:
                make_primary = True
            else:
                return
            self.db.add_bid_moraware_link(
                selected_bid_id,
                str(job_id).strip(),
                (job_number or "").strip(),
                make_primary=make_primary,
                job_name=(job_name or "").strip(),
            )
        else:
            self.db.add_bid_moraware_link(
                selected_bid_id,
                str(job_id).strip(),
                (job_number or "").strip(),
                make_primary=True,
                job_name=(job_name or "").strip(),
            )

        mw_job_number = (job_number or "").strip()
        if not already_linked:
            self.db.set_moraware_job_number(selected_bid_id, mw_job_number or "")
        # Always overwrite local team fields from Moraware on link.
        self.db.set_bid_sales_team(
            selected_bid_id,
            salesperson=(moraware_salesperson or "").strip(),
            project_manager=(moraware_project_manager or "").strip(),
        )
        mw_label = f"#{mw_job_number}" if mw_job_number else f"ID {job_id}"
        self._render_rows(
            update_status=True,
            status_prefix=(
                f"Linked '{selected_bid.get('bid_name') or 'bid'}' to Moraware job {mw_label}."
            )
        )
        self._maybe_prompt_split_after_multilink(int(selected_bid_id))

        for idx, row in enumerate(self._display_rows):
            if row.get("job_id") == str(job_id).strip():
                self.table.selectRow(idx)
                self._show_detail_for_row(idx)
                break

    def _maybe_prompt_split_after_multilink(self, bid_id: int):
        links = self.db.get_bid_moraware_links(bid_id)
        bid = self.db.get_bid_by_id(bid_id) or {}
        if len(links) < 2:
            return
        if str((bid.get("bid_role") or "normal")).strip().lower() == "child":
            return
        reply = QMessageBox.question(
            self,
            "Split Linked Jobs",
            "Multiple Moraware jobs are linked to this quote.\n\nSplit now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return
        dlg = SplitMorawareAllocationDialog(self.db, bid_id, self)
        if dlg.exec_() and getattr(dlg, "did_split", False):
            self._selected_bid_id = None
            self.detail_panel.hide()
            self.unlinked_detail_label.hide()
            self._render_rows(update_status=True, status_prefix=f"Bid '{bid.get('bid_name') or bid_id}' split into child bids.")

    def _unsync_from_moraware(self, bid_id: int):
        bid = self.db.get_bid_by_id(bid_id) or {}
        if not bid:
            return
        reply = QMessageBox.question(
            self,
            "Unsync from Moraware",
            f"Unsync '{bid.get('bid_name') or bid_id}' from Moraware?\n\n"
            "This removes Moraware links and synced invoice rows, but keeps the bid status.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.db.unsync_bid_from_moraware(bid_id)
        self._selected_bid_id = None
        self.detail_panel.hide()
        self.unlinked_detail_label.hide()
        self._render_rows(update_status=True, status_prefix="Unsynced selected bid from Moraware.")

    def _add_another_job_to_quote(self, bid_id: int, exclude_job_id: str = ""):
        linked = self.db.get_bid_moraware_links(bid_id)
        linked_ids = {str((x or {}).get("moraware_job_id") or "").strip() for x in linked}
        options = []
        label_to_job = {}
        for row in self._display_rows:
            jid = str((row or {}).get("job_id") or "").strip()
            if not jid or jid == str(exclude_job_id or "").strip() or jid in linked_ids:
                continue
            job = (row or {}).get("job") or {}
            jn = (job.get("job_number") or "").strip()
            name = (job.get("name") or "").strip()
            label = f"#{jn} — {name}" if jn else f"ID {jid} — {name}"
            options.append(label)
            label_to_job[label] = {
                "job_id": jid,
                "job_number": jn,
                "job_name": name,
                "job_account": (job.get("account") or "").strip(),
                "salesperson": (job.get("salesperson") or "").strip(),
                "project_manager": (job.get("project_manager") or "").strip(),
            }
        if not options:
            QMessageBox.information(self, "No Additional Jobs", "No other visible Moraware jobs are available to add to this quote.")
            return
        picked, ok = QInputDialog.getItem(
            self,
            "Add Another Job",
            "Choose an additional Moraware job to link to this quote:",
            options,
            0,
            False,
        )
        if not ok or not picked:
            return
        payload = label_to_job.get(picked) or {}
        self._link_to_local_bid(
            payload.get("job_id") or "",
            payload.get("job_number") or "",
            payload.get("job_name") or "",
            payload.get("job_account") or "",
            payload.get("salesperson") or "",
            payload.get("project_manager") or "",
            target_bid_id=bid_id,
        )

    def _edit_split_allocation(self, bid_id: int):
        dlg = SplitMorawareAllocationDialog(self.db, bid_id, self)
        if dlg.exec_():
            self._render_rows()
            self.detail_panel.load_bid(self.db, bid_id)

    def _split_bid_from_moraware(self, bid_id: int):
        bid = self.db.get_bid_by_id(bid_id) or {}
        reply = QMessageBox.question(
            self,
            "Split Bid",
            "This will create child bids (one per linked Moraware job) and hide the parent from rollups.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        dlg = SplitMorawareAllocationDialog(self.db, bid_id, self)
        if dlg.exec_() and getattr(dlg, "did_split", False):
            self._selected_bid_id = None
            self.detail_panel.hide()
            self.unlinked_detail_label.hide()
            self._render_rows(update_status=True, status_prefix=f"Bid '{bid.get('bid_name') or bid_id}' split into child bids.")

    def _open_in_moraware(self, job_id: str):
        configured_url = (get_config().get("moraware_url") or "").strip()
        parsed = urlparse(configured_url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
        if not origin:
            QMessageBox.warning(self, "Moraware URL Missing", "Set your Moraware URL in Settings first.")
            return
        webbrowser.open(f"{origin}/sys/job/{job_id}")

    def _edit_job(self, bid_id: int):
        dlg = PMEditJobDialog(self.db, bid_id, self)
        if dlg.exec_() and dlg.selected_customer_id:
            self.db.update_won_details(
                bid_id,
                dlg.selected_customer_id,
                salesperson=dlg.salesperson,
                project_manager=dlg.project_manager,
                won_notes=dlg.won_notes,
                est_complete_date=dlg.est_complete_date,
                est_complete_date_manual=dlg.est_complete_date_manual,
                est_start_month=dlg.est_start_month,
                won_date=dlg.won_date,
            )
            self._render_rows()
            self.detail_panel.load_bid(self.db, bid_id)

    def _move_back_to_bidding(self, bid_id: int):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return
        reply = QMessageBox.question(
            self,
            "Move Back to Bidding",
            f"Move '{bid['bid_name']}' back to PENDING status?\n\n"
            "This will clear won details and invoice data.\n"
            "Use 'Unsync from Moraware' if you only want to remove Moraware linkage.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.move_bid_back_to_bidding(bid_id)
            self._selected_bid_id = None
            self.detail_panel.hide()
            self.unlinked_detail_label.hide()
            self._render_rows()

    def _sync_single_bid(self, bid_id: int):
        cfg = get_config()
        if not all([cfg.get("moraware_username"), cfg.get("moraware_password"), cfg.get("moraware_url")]):
            QMessageBox.warning(self, "Moraware Not Configured", "Configure Moraware credentials in Settings.")
            return
        self._set_sync_buttons_enabled(False)
        self._sync_worker = InvoiceSyncWorker(self.db, single_bid_id=bid_id)
        self._sync_worker.finished.connect(lambda _jobs, _phases: self._on_single_sync_done(bid_id))
        self._sync_worker.error.connect(self._on_sync_error)
        self._sync_worker.start()

    def _sync_all_linked(self):
        cfg = get_config()
        if not all([cfg.get("moraware_username"), cfg.get("moraware_password"), cfg.get("moraware_url")]):
            QMessageBox.warning(self, "Moraware Not Configured", "Configure Moraware credentials in Settings.")
            return
        self._set_sync_buttons_enabled(False)
        self._sync_worker = InvoiceSyncWorker(self.db)
        self._sync_worker.finished.connect(self._on_sync_all_done)
        self._sync_worker.error.connect(self._on_sync_error)
        self._sync_worker.start()

    def _on_sync_all_done(self, jobs_synced, phases_found):
        self._set_sync_buttons_enabled(True)
        self._render_rows()
        if self._selected_bid_id:
            self.detail_panel.load_bid(self.db, self._selected_bid_id)
        self.status_label.setText(f"Refresh complete: {jobs_synced} jobs, {phases_found} phases.")

    def _on_single_sync_done(self, bid_id: int):
        self._set_sync_buttons_enabled(True)
        self._render_rows()
        self.detail_panel.load_bid(self.db, bid_id)
        self.status_label.setText("Selected job refresh complete.")

    def _on_sync_error(self, error_msg: str):
        self._set_sync_buttons_enabled(True)
        QMessageBox.critical(self, "Sync Error", f"Invoice sync failed:\n{error_msg}")

    def _set_sync_buttons_enabled(self, enabled: bool):
        self.sync_all_btn.setEnabled(enabled)
        self.sync_all_btn.setText("Refresh All Jobs" if enabled else "Refreshing...")

    def _on_detail_action(self, action, bid_id):
        if action == "edit_won":
            self._edit_job(bid_id)
        elif action == "refresh_invoices":
            self._sync_single_bid(bid_id)
        elif action == "move_back":
            self._move_back_to_bidding(bid_id)
        elif action == "open_bid_folder":
            self._open_bid_folder(bid_id)

    def _open_bid_folder(self, bid_id):
        bid = self.db.get_bid_by_id(bid_id)
        if not bid:
            return
        original_bid_date = bid.get("original_bid_date")
        if not original_bid_date:
            QMessageBox.warning(self, "Missing Bid Date", "This bid has no original bid date.")
            return
        try:
            bid_date = datetime.strptime(original_bid_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Invalid Bid Date", f"Could not parse original bid date: {original_bid_date}")
            return

        cfg = get_config()
        dropbox_bids_path = (cfg.get("dropbox_bids_path") or "").strip()
        if not dropbox_bids_path:
            QMessageBox.warning(self, "Dropbox Path Not Configured", "Set Dropbox bids root path in Settings first.")
            return

        year_path = os.path.join(dropbox_bids_path, str(bid_date.year))
        if not os.path.isdir(year_path):
            QMessageBox.warning(self, "Folder Not Found", f"Year folder not found:\n{year_path}")
            return

        month_folder_map = {
            1: "1- January",
            2: "2 -February",
            3: "3 - March",
            4: "4 - April",
            5: "5 - May",
            6: "6 - June",
            7: "7 - July",
            8: "8 - August",
            9: "9 - September",
            10: "10 - October",
            11: "11 - November",
            12: "12- December",
        }
        month_path = os.path.join(year_path, month_folder_map[bid_date.month])
        if not os.path.isdir(month_path):
            month_name = bid_date.strftime("%B").lower()
            fallback = None
            for entry in os.listdir(year_path):
                candidate = os.path.join(year_path, entry)
                if not os.path.isdir(candidate):
                    continue
                normalized = entry.replace("-", " ").replace("_", " ").lower()
                if normalized.startswith(str(bid_date.month)) and month_name in normalized:
                    fallback = candidate
                    break
            if fallback:
                month_path = fallback

        if not os.path.isdir(month_path):
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Could not find month folder for {bid_date.strftime('%B %Y')}.\nExpected:\n{month_path}",
            )
            return
        os.startfile(month_path)
