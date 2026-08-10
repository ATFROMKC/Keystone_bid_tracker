"""
Keystone Bid Tracker - Settings Tab
Database path config, test connection, version info, rebuild stats.
"""

import os
import sqlite3

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QFrame, QScrollArea,
    QComboBox, QColorDialog, QDateEdit, QDialog,
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate

from config import (
    get_config, save_config, get_database_path, set_database_path,
    get_current_estimator, set_current_estimator, _auto_color_for,
    get_bid_board_files_path, set_bid_board_files_path,
    get_outlook_sync_config, save_outlook_sync_config,
)
from utils.outlook_sync_worker import (
    OutlookListCalendarsWorker, OutlookTestWorker, OutlookSyncWorker,
)


APP_VERSION = "1.0.0"


class MorewareTestWorker(QThread):
    """Background thread to test Moraware login without blocking the UI."""
    finished = pyqtSignal(bool, str)

    def __init__(self, url, username, password):
        super().__init__()
        self.url = url
        self.username = username
        self.password = password

    def run(self):
        try:
            from utils.moraware_client import MorewareClient
            client = MorewareClient(self.username, self.password, self.url)
            client.login()
            self.finished.emit(True, "Logged in to Moraware successfully.")
        except Exception as e:
            self.finished.emit(False, str(e))


class MorewareDiagWorker(QThread):
    """Background thread to dump Moraware page HTML for debugging."""
    finished = pyqtSignal(bool, str)

    def __init__(self, url, username, password, output_dir):
        super().__init__()
        self.url = url
        self.username = username
        self.password = password
        self.output_dir = output_dir

    def run(self):
        try:
            from utils.moraware_client import MorewareClient
            client = MorewareClient(self.username, self.password, self.url)
            summary = client.dump_diagnostics(self.output_dir)
            self.finished.emit(True, summary)
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self._load_moraware_fields()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setObjectName("headingLabel")
        layout.addWidget(title)

        # Database path section
        db_frame = QFrame()
        db_frame.setObjectName("card")
        db_layout = QVBoxLayout(db_frame)
        db_layout.setContentsMargins(20, 16, 20, 16)
        db_layout.setSpacing(12)

        db_title = QLabel("Database Location")
        db_title.setObjectName("subheadingLabel")
        db_layout.addWidget(db_title)

        db_desc = QLabel("Path to the shared SQLite database file (should be in Dropbox)")
        db_desc.setObjectName("secondaryLabel")
        db_desc.setWordWrap(True)
        db_layout.addWidget(db_desc)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(get_database_path())
        self.path_input.setReadOnly(True)
        path_row.addWidget(self.path_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(browse_btn)
        db_layout.addLayout(path_row)

        btn_row = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("primaryButton")
        test_btn.clicked.connect(self._on_test)
        btn_row.addWidget(test_btn)

        save_btn = QPushButton("Save Path")
        save_btn.clicked.connect(self._on_save_path)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        db_layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        db_layout.addWidget(self.status_label)

        layout.addWidget(db_frame)

        # Dropbox bids path section
        dropbox_frame = QFrame()
        dropbox_frame.setObjectName("card")
        dropbox_layout = QVBoxLayout(dropbox_frame)
        dropbox_layout.setContentsMargins(20, 16, 20, 16)
        dropbox_layout.setSpacing(12)

        dropbox_title = QLabel("Dropbox Bids Folder")
        dropbox_title.setObjectName("subheadingLabel")
        dropbox_layout.addWidget(dropbox_title)

        dropbox_desc = QLabel("Root bids folder used for opening year/month bid folders from Awarded tab")
        dropbox_desc.setObjectName("secondaryLabel")
        dropbox_desc.setWordWrap(True)
        dropbox_layout.addWidget(dropbox_desc)

        dropbox_row = QHBoxLayout()
        self.dropbox_path_input = QLineEdit()
        self.dropbox_path_input.setPlaceholderText(r"C:\Users\you\Dropbox\~Bids")
        dropbox_row.addWidget(self.dropbox_path_input, 1)

        dropbox_browse_btn = QPushButton("Browse...")
        dropbox_browse_btn.clicked.connect(self._on_browse_dropbox)
        dropbox_row.addWidget(dropbox_browse_btn)
        dropbox_layout.addLayout(dropbox_row)

        dropbox_btn_row = QHBoxLayout()
        dropbox_save_btn = QPushButton("Save Dropbox Path")
        dropbox_save_btn.clicked.connect(self._on_save_dropbox_path)
        dropbox_btn_row.addWidget(dropbox_save_btn)
        dropbox_btn_row.addStretch()
        dropbox_layout.addLayout(dropbox_btn_row)

        self.dropbox_status_label = QLabel("")
        self.dropbox_status_label.setWordWrap(True)
        dropbox_layout.addWidget(self.dropbox_status_label)

        layout.addWidget(dropbox_frame)

        # Bid Board (Calendar) section
        layout.addWidget(self._build_bid_board_card())
        layout.addWidget(self._build_outlook_sync_card())

        # Moraware Integration section
        mw_frame = QFrame()
        mw_frame.setObjectName("card")
        mw_layout = QVBoxLayout(mw_frame)
        mw_layout.setContentsMargins(20, 16, 20, 16)
        mw_layout.setSpacing(12)

        mw_title = QLabel("Moraware Integration")
        mw_title.setObjectName("subheadingLabel")
        mw_layout.addWidget(mw_title)

        mw_desc = QLabel("Connect to Moraware for job matching and invoice sync")
        mw_desc.setObjectName("secondaryLabel")
        mw_desc.setWordWrap(True)
        mw_layout.addWidget(mw_desc)

        url_row = QHBoxLayout()
        url_label = QLabel("Moraware URL:")
        url_label.setFixedWidth(120)
        url_row.addWidget(url_label)
        self.mw_url_input = QLineEdit()
        self.mw_url_input.setPlaceholderText("https://your-company.moraware.net")
        url_row.addWidget(self.mw_url_input, 1)
        mw_layout.addLayout(url_row)

        user_row = QHBoxLayout()
        user_label = QLabel("Username:")
        user_label.setFixedWidth(120)
        user_row.addWidget(user_label)
        self.mw_user_input = QLineEdit()
        self.mw_user_input.setPlaceholderText("Your Moraware username")
        user_row.addWidget(self.mw_user_input, 1)
        mw_layout.addLayout(user_row)

        pass_row = QHBoxLayout()
        pass_label = QLabel("Password:")
        pass_label.setFixedWidth(120)
        pass_row.addWidget(pass_label)
        self.mw_pass_input = QLineEdit()
        self.mw_pass_input.setEchoMode(QLineEdit.Password)
        self.mw_pass_input.setPlaceholderText("Your Moraware password")
        pass_row.addWidget(self.mw_pass_input, 1)
        mw_layout.addLayout(pass_row)

        mw_btn_row = QHBoxLayout()
        mw_test_btn = QPushButton("Test Connection")
        mw_test_btn.setObjectName("primaryButton")
        mw_test_btn.clicked.connect(self._on_test_moraware)
        mw_btn_row.addWidget(mw_test_btn)

        mw_save_btn = QPushButton("Save Credentials")
        mw_save_btn.clicked.connect(self._on_save_moraware)
        mw_btn_row.addWidget(mw_save_btn)

        mw_diag_btn = QPushButton("Run Diagnostics")
        mw_diag_btn.setToolTip("Saves raw HTML from Moraware pages for debugging selectors")
        mw_diag_btn.clicked.connect(self._on_run_diagnostics)
        mw_btn_row.addWidget(mw_diag_btn)
        mw_btn_row.addStretch()
        mw_layout.addLayout(mw_btn_row)

        self.mw_status_label = QLabel("")
        self.mw_status_label.setWordWrap(True)
        mw_layout.addWidget(self.mw_status_label)

        layout.addWidget(mw_frame)

        # Legacy tools (kept out of the Estimator portal tab bar)
        legacy_frame = QFrame()
        legacy_frame.setObjectName("card")
        legacy_layout = QVBoxLayout(legacy_frame)
        legacy_layout.setContentsMargins(20, 16, 20, 16)
        legacy_layout.setSpacing(12)

        legacy_title = QLabel("Legacy Tools")
        legacy_title.setObjectName("subheadingLabel")
        legacy_layout.addWidget(legacy_title)

        legacy_desc = QLabel(
            "One-time Excel backlog import from the old Bid Tracker spreadsheet. "
            "Hidden from the Estimator portal — open here only when you need it."
        )
        legacy_desc.setObjectName("secondaryLabel")
        legacy_desc.setWordWrap(True)
        legacy_layout.addWidget(legacy_desc)

        excel_import_btn = QPushButton("Open Excel Import…")
        excel_import_btn.setToolTip("Import historical bids from Bid_Tracker_Backlog.xlsx")
        excel_import_btn.clicked.connect(self._open_excel_import)
        excel_import_btn.setFixedWidth(180)
        legacy_layout.addWidget(excel_import_btn)

        layout.addWidget(legacy_frame)

        # Maintenance section
        maint_frame = QFrame()
        maint_frame.setObjectName("card")
        maint_layout = QVBoxLayout(maint_frame)
        maint_layout.setContentsMargins(20, 16, 20, 16)
        maint_layout.setSpacing(12)

        maint_title = QLabel("Maintenance")
        maint_title.setObjectName("subheadingLabel")
        maint_layout.addWidget(maint_title)

        rebuild_btn = QPushButton("Rebuild Stats")
        rebuild_btn.setToolTip("Recalculates any cached values and verifies database integrity")
        rebuild_btn.clicked.connect(self._on_rebuild)
        rebuild_btn.setFixedWidth(160)
        maint_layout.addWidget(rebuild_btn)

        self.rebuild_label = QLabel("")
        maint_layout.addWidget(self.rebuild_label)

        layout.addWidget(maint_frame)

        # Version info
        ver_frame = QFrame()
        ver_frame.setObjectName("card")
        ver_layout = QVBoxLayout(ver_frame)
        ver_layout.setContentsMargins(20, 16, 20, 16)
        ver_layout.setSpacing(8)

        ver_title = QLabel("About")
        ver_title.setObjectName("subheadingLabel")
        ver_layout.addWidget(ver_title)

        ver_label = QLabel(f"Keystone Bid Tracker  v{APP_VERSION}")
        ver_layout.addWidget(ver_label)

        ver_desc = QLabel("Built for Keystone Solid Surfaces")
        ver_desc.setObjectName("secondaryLabel")
        ver_layout.addWidget(ver_desc)

        layout.addWidget(ver_frame)
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _build_bid_board_card(self):
        frame = QFrame()
        frame.setObjectName("card")
        v = QVBoxLayout(frame)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        title = QLabel("Bid Board")
        title.setObjectName("subheadingLabel")
        v.addWidget(title)

        desc = QLabel(
            "Shared estimator roster and colors (saved in the database so both PCs match). "
            "'My estimator' is this computer only, used by Assign to Me. "
            "Completed cards always use universal blue."
        )
        desc.setObjectName("secondaryLabel")
        desc.setWordWrap(True)
        v.addWidget(desc)

        me_row = QHBoxLayout()
        me_label = QLabel("My estimator (this PC):")
        me_label.setFixedWidth(160)
        me_row.addWidget(me_label)
        self.current_estimator_combo = QComboBox()
        self.current_estimator_combo.setEditable(True)
        self.current_estimator_combo.setInsertPolicy(QComboBox.NoInsert)
        me_row.addWidget(self.current_estimator_combo, 1)
        me_save_btn = QPushButton("Save")
        me_save_btn.clicked.connect(self._on_save_current_estimator)
        me_row.addWidget(me_save_btn)
        v.addLayout(me_row)

        roster_label = QLabel("Estimator roster")
        roster_label.setObjectName("secondaryLabel")
        v.addWidget(roster_label)

        self.estimator_roster_container = QVBoxLayout()
        self.estimator_roster_container.setSpacing(6)
        v.addLayout(self.estimator_roster_container)

        add_row = QHBoxLayout()
        self.new_estimator_input = QLineEdit()
        self.new_estimator_input.setPlaceholderText("New estimator name...")
        add_row.addWidget(self.new_estimator_input, 1)
        add_est_btn = QPushButton("Add estimator")
        add_est_btn.clicked.connect(self._on_add_estimator)
        add_row.addWidget(add_est_btn)
        pull_btn = QPushButton("Pull estimators from bids")
        pull_btn.clicked.connect(self._on_pull_estimators)
        add_row.addWidget(pull_btn)
        v.addLayout(add_row)

        files_label = QLabel("Bid Board attachments folder")
        files_label.setObjectName("secondaryLabel")
        v.addWidget(files_label)
        files_row = QHBoxLayout()
        self.board_files_input = QLineEdit()
        self.board_files_input.setPlaceholderText(r"Defaults to <database folder>\BidBoardFiles")
        files_row.addWidget(self.board_files_input, 1)
        files_browse = QPushButton("Browse...")
        files_browse.clicked.connect(self._on_browse_board_files)
        files_row.addWidget(files_browse)
        files_save = QPushButton("Save")
        files_save.clicked.connect(self._on_save_board_files)
        files_row.addWidget(files_save)
        v.addLayout(files_row)

        self.bid_board_status_label = QLabel("")
        self.bid_board_status_label.setWordWrap(True)
        v.addWidget(self.bid_board_status_label)

        self._load_bid_board_settings()
        return frame

    def _build_outlook_sync_card(self):
        frame = QFrame()
        frame.setObjectName("card")
        v = QVBoxLayout(frame)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        title = QLabel("Outlook Sync (read-only)")
        title.setObjectName("subheadingLabel")
        v.addWidget(title)

        self.outlook_desc_label = QLabel("")
        self.outlook_desc_label.setObjectName("secondaryLabel")
        self.outlook_desc_label.setWordWrap(True)
        v.addWidget(self.outlook_desc_label)

        src_row = QHBoxLayout()
        src_row.addWidget(QLabel("Outlook source:"))
        self.outlook_provider_combo = QComboBox()
        self.outlook_provider_combo.addItem("Local Outlook Desktop", "desktop")
        self.outlook_provider_combo.addItem("Microsoft Graph", "graph")
        self.outlook_provider_combo.currentIndexChanged.connect(self._on_outlook_provider_changed)
        src_row.addWidget(self.outlook_provider_combo, 1)
        src_row.addStretch()
        v.addLayout(src_row)

        self.outlook_graph_ids_widget = QWidget()
        id_row = QHBoxLayout(self.outlook_graph_ids_widget)
        id_row.setContentsMargins(0, 0, 0, 0)
        self.outlook_tenant_input = QLineEdit()
        self.outlook_tenant_input.setPlaceholderText("Directory (tenant) ID")
        id_row.addWidget(self.outlook_tenant_input, 1)
        self.outlook_client_input = QLineEdit()
        self.outlook_client_input.setPlaceholderText("Application (client) ID")
        id_row.addWidget(self.outlook_client_input, 1)
        save_ids = QPushButton("Save IDs")
        save_ids.clicked.connect(self._on_save_outlook_ids)
        id_row.addWidget(save_ids)
        v.addWidget(self.outlook_graph_ids_widget)

        btn_row = QHBoxLayout()
        self.outlook_signin_btn = QPushButton("Sign in to Microsoft 365")
        self.outlook_signin_btn.clicked.connect(self._on_outlook_signin)
        btn_row.addWidget(self.outlook_signin_btn)
        self.outlook_signout_btn = QPushButton("Sign out")
        self.outlook_signout_btn.clicked.connect(self._on_outlook_signout)
        btn_row.addWidget(self.outlook_signout_btn)
        refresh_cals = QPushButton("Refresh calendars")
        refresh_cals.clicked.connect(self._on_outlook_refresh_calendars)
        btn_row.addWidget(refresh_cals)
        btn_row.addStretch()
        v.addLayout(btn_row)

        cal_row = QHBoxLayout()
        cal_row.addWidget(QLabel("Shared calendar:"))
        self.outlook_calendar_combo = QComboBox()
        self.outlook_calendar_combo.setMinimumWidth(280)
        cal_row.addWidget(self.outlook_calendar_combo, 1)
        use_cal = QPushButton("Use selected")
        use_cal.clicked.connect(self._on_save_outlook_calendar)
        cal_row.addWidget(use_cal)
        v.addLayout(cal_row)

        test_row = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("primaryButton")
        test_btn.clicked.connect(self._on_outlook_test)
        test_row.addWidget(test_btn)
        test_row.addStretch()
        v.addLayout(test_row)

        win_row = QHBoxLayout()
        win_row.addWidget(QLabel("Default Sync Outlook:"))
        self.outlook_sync_window_combo = QComboBox()
        self.outlook_sync_window_combo.addItem(
            "This week onward (skip older completed work)", "week_onward"
        )
        self.outlook_sync_window_combo.addItem(
            "Last 60 days + upcoming 120", "rolling"
        )
        self.outlook_sync_window_combo.currentIndexChanged.connect(
            self._on_outlook_sync_window_changed
        )
        win_row.addWidget(self.outlook_sync_window_combo, 1)
        v.addLayout(win_row)

        imp_label = QLabel("One-time import range (does not change default Sync)")
        imp_label.setObjectName("secondaryLabel")
        v.addWidget(imp_label)
        imp_row = QHBoxLayout()
        self.outlook_import_start = QDateEdit()
        self.outlook_import_start.setCalendarPopup(True)
        self.outlook_import_start.setDisplayFormat("MM/dd/yyyy")
        self.outlook_import_end = QDateEdit()
        self.outlook_import_end.setCalendarPopup(True)
        self.outlook_import_end.setDisplayFormat("MM/dd/yyyy")
        today = QDate.currentDate()
        self.outlook_import_start.setDate(today.addDays(-60))
        self.outlook_import_end.setDate(today.addDays(120))
        imp_row.addWidget(QLabel("Start"))
        imp_row.addWidget(self.outlook_import_start)
        imp_row.addWidget(QLabel("End"))
        imp_row.addWidget(self.outlook_import_end)
        preset_btn = QPushButton("Last 60 days + upcoming")
        preset_btn.clicked.connect(self._on_outlook_preset_range)
        imp_row.addWidget(preset_btn)
        week_btn = QPushButton("This week onward")
        week_btn.clicked.connect(self._on_outlook_week_preset)
        imp_row.addWidget(week_btn)
        import_btn = QPushButton("Import range")
        import_btn.clicked.connect(self._on_outlook_import_range)
        imp_row.addWidget(import_btn)
        imp_row.addStretch()
        v.addLayout(imp_row)

        self.outlook_status_label = QLabel("")
        self.outlook_status_label.setWordWrap(True)
        v.addWidget(self.outlook_status_label)

        self._outlook_calendars = []
        self._outlook_provider_ready = False
        self._load_outlook_settings()
        return frame

    def _outlook_provider(self) -> str:
        data = self.outlook_provider_combo.currentData()
        return data if data in ("desktop", "graph") else "desktop"

    def _apply_outlook_provider_ui(self):
        is_graph = self._outlook_provider() == "graph"
        self.outlook_graph_ids_widget.setVisible(is_graph)
        self.outlook_signin_btn.setVisible(is_graph)
        self.outlook_signout_btn.setVisible(is_graph)
        if is_graph:
            self.outlook_desc_label.setText(
                "One-way import from the shared Outlook bid calendar into Bid Board. "
                "Microsoft Graph requests Calendars.Read.Shared (and User.Read) only. "
                "It cannot create, edit, or delete Outlook events. "
                "If sign-in says consent is blocked, an admin must approve those read "
                "permissions — still no write access."
            )
        else:
            self.outlook_desc_label.setText(
                "One-way import from Classic Outlook on this PC into Bid Board. "
                "Uses your already signed-in Outlook profile — no Microsoft password "
                "or tenant/client IDs. Bid Tracker only reads appointments; it never "
                "creates, edits, or deletes Outlook events. "
                "Sync can fill empty Actual Due Date / Accounts from appointment text "
                "(Subject, Location, and Body when Outlook allows). "
                "If Body reads hang, allow programmatic access in Outlook Trust Center, "
                "or sync still works from Subject/Location alone."
            )

    def _on_outlook_provider_changed(self):
        if not getattr(self, "_outlook_provider_ready", False):
            return
        save_outlook_sync_config({"provider": self._outlook_provider()})
        self._apply_outlook_provider_ui()
        self.outlook_status_label.setText(
            "Source saved. Refresh calendars and select Commercial Bid."
        )

    def _calendar_combo_label(self, cal: dict) -> str:
        name = cal.get("name") or "(unnamed)"
        owner = ""
        ow = cal.get("owner")
        if isinstance(ow, dict):
            owner = (ow.get("name") or ow.get("address") or "").strip()
        elif ow:
            owner = str(ow).strip()
        path = (cal.get("path") or "").strip()
        bits = [b for b in (owner, path) if b]
        if bits:
            return f"{name}  ({' · '.join(bits)})"
        return name

    def _load_outlook_settings(self):
        cfg = get_outlook_sync_config()
        self._outlook_provider_ready = False
        provider = cfg.get("provider") or "desktop"
        idx = self.outlook_provider_combo.findData(provider)
        if idx < 0:
            idx = 0
        self.outlook_provider_combo.setCurrentIndex(idx)
        win_idx = self.outlook_sync_window_combo.findData(cfg.get("sync_window") or "week_onward")
        self.outlook_sync_window_combo.blockSignals(True)
        self.outlook_sync_window_combo.setCurrentIndex(win_idx if win_idx >= 0 else 0)
        self.outlook_sync_window_combo.blockSignals(False)
        self._outlook_provider_ready = True
        self._apply_outlook_provider_ui()
        self.outlook_tenant_input.setText(cfg.get("tenant_id") or "")
        self.outlook_client_input.setText(cfg.get("client_id") or "")
        self.outlook_calendar_combo.clear()
        name = cfg.get("calendar_name") or ""
        owner = cfg.get("calendar_owner") or ""
        path = cfg.get("calendar_path") or ""
        cid = cfg.get("calendar_id") or ""
        if cid:
            fake = {"name": name or cid[:20], "owner": {"name": owner}, "path": path}
            self.outlook_calendar_combo.addItem(self._calendar_combo_label(fake), cid)
        last = cfg.get("last_synced_at") or ""
        if last:
            self.outlook_status_label.setText(f"Last synced: {last}")

    def _on_save_outlook_ids(self):
        save_outlook_sync_config({
            "tenant_id": self.outlook_tenant_input.text().strip(),
            "client_id": self.outlook_client_input.text().strip(),
        })
        self.outlook_status_label.setText("Saved tenant and client IDs on this PC.")

    def _on_outlook_signin(self):
        self._on_save_outlook_ids()
        self.outlook_status_label.setText("Signing in… a browser window may open.")
        try:
            from utils.outlook_graph_client import OutlookGraphClient, OutlookAuthError, CONSENT_HINT
            cfg = get_outlook_sync_config()
            client = OutlookGraphClient(cfg["tenant_id"], cfg["client_id"])
            client.acquire_token(interactive=True)
            me = client.get_me()
            name = me.get("displayName") or me.get("userPrincipalName") or "Signed in"
            self.outlook_status_label.setText(f"Signed in as {name}.")
            self._on_outlook_refresh_calendars()
        except OutlookAuthError as e:
            msg = (CONSENT_HINT + "\n\nDetails: " + str(e)) if e.consent_required else str(e)
            self.outlook_status_label.setText(msg)
            QMessageBox.warning(self, "Outlook sign-in", msg)
        except Exception as e:
            self.outlook_status_label.setText(str(e))
            QMessageBox.warning(self, "Outlook sign-in", str(e))

    def _on_outlook_signout(self):
        import os
        from utils.outlook_graph_client import token_cache_path
        try:
            cfg = get_outlook_sync_config()
            if cfg.get("tenant_id") and cfg.get("client_id"):
                from utils.outlook_graph_client import OutlookGraphClient
                OutlookGraphClient(cfg["tenant_id"], cfg["client_id"]).sign_out()
        except Exception:
            p = token_cache_path()
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        self.outlook_status_label.setText("Signed out. Tokens cleared on this PC.")

    def _on_outlook_refresh_calendars(self):
        self.outlook_status_label.setText("Loading calendars…")
        self._outlook_list_worker = OutlookListCalendarsWorker()
        self._outlook_list_worker.finished.connect(self._on_outlook_calendars_loaded)
        self._outlook_list_worker.start()

    def _on_outlook_calendars_loaded(self, ok, msg, cals):
        if not ok:
            self.outlook_status_label.setText(msg)
            QMessageBox.warning(self, "Outlook calendars", msg)
            return
        self._outlook_calendars = cals or []
        current_id = get_outlook_sync_config().get("calendar_id") or ""
        self.outlook_calendar_combo.clear()
        select_idx = 0
        for i, cal in enumerate(self._outlook_calendars):
            self.outlook_calendar_combo.addItem(self._calendar_combo_label(cal), cal.get("id"))
            if cal.get("id") == current_id:
                select_idx = i
        if self.outlook_calendar_combo.count():
            self.outlook_calendar_combo.setCurrentIndex(select_idx)
        self.outlook_status_label.setText(msg)

    def _on_save_outlook_calendar(self):
        cid = self.outlook_calendar_combo.currentData()
        if not cid:
            QMessageBox.warning(self, "Outlook calendar", "Select a calendar first.")
            return
        cal = next((c for c in (self._outlook_calendars or []) if c.get("id") == cid), None)
        if cal:
            name = cal.get("name") or ""
            ow = cal.get("owner") or {}
            owner = (ow.get("name") or ow.get("address") or "") if isinstance(ow, dict) else str(ow or "")
            path = cal.get("path") or ""
            store_id = cal.get("store_id") or ""
        else:
            label = self.outlook_calendar_combo.currentText()
            name, owner, path, store_id = label, "", "", ""
            if "  (" in label and label.endswith(")"):
                name, rest = label.rsplit("  (", 1)
                owner = rest[:-1]
        save_outlook_sync_config({
            "provider": self._outlook_provider(),
            "calendar_id": cid,
            "calendar_name": (name or "").strip(),
            "calendar_owner": (owner or "").strip(),
            "calendar_path": (path or "").strip(),
            "calendar_store_id": (store_id or "").strip(),
        })
        self.outlook_status_label.setText(f"Using calendar: {(name or cid).strip()}")

    def _on_outlook_test(self):
        self._on_save_outlook_calendar()
        self.outlook_status_label.setText("Testing read-only calendar access…")
        self._outlook_test_worker = OutlookTestWorker()
        self._outlook_test_worker.finished.connect(self._on_outlook_test_done)
        self._outlook_test_worker.start()

    def _on_outlook_test_done(self, ok, msg):
        self.outlook_status_label.setText(msg)
        if not ok:
            QMessageBox.warning(self, "Test Connection", msg)
        else:
            QMessageBox.information(self, "Test Connection", msg)

    def _on_outlook_preset_range(self):
        today = QDate.currentDate()
        self.outlook_import_start.setDate(today.addDays(-60))
        self.outlook_import_end.setDate(today.addDays(120))

    def _on_outlook_week_preset(self):
        today = QDate.currentDate()
        monday = today.addDays(-today.dayOfWeek() + 1)  # Qt Monday=1
        self.outlook_import_start.setDate(monday)
        self.outlook_import_end.setDate(today.addDays(120))

    def _on_outlook_sync_window_changed(self):
        if not getattr(self, "_outlook_provider_ready", False):
            return
        mode = self.outlook_sync_window_combo.currentData() or "week_onward"
        save_outlook_sync_config({"sync_window": mode})
        if mode == "week_onward":
            self.outlook_status_label.setText(
                "Sync Outlook will read this week onward (not older history)."
            )
        else:
            self.outlook_status_label.setText(
                "Sync Outlook will read the last 60 days plus upcoming 120 days."
            )

    def _on_outlook_import_range(self):
        self._on_save_outlook_calendar()
        sd = self.outlook_import_start.date().toPyDate()
        ed = self.outlook_import_end.date().toPyDate()
        self.outlook_status_label.setText("Importing Outlook events (read-only)…")
        self._outlook_import_worker = OutlookSyncWorker(self.db, sd, ed)
        self._outlook_import_worker.finished.connect(self._on_outlook_import_done)
        self._outlook_import_worker.start()

    def _on_outlook_import_done(self, ok, msg, result):
        self.outlook_status_label.setText(msg)
        if not ok:
            QMessageBox.warning(self, "Outlook import", msg)
            return
        due_applied = 0
        account_applied = 0
        candidates = (result or {}).get("hint_candidates") or []
        if candidates:
            from ui.outlook_hint_review_dialog import OutlookHintReviewDialog
            review = OutlookHintReviewDialog(candidates, self)
            if review.exec_() == QDialog.Accepted:
                for row in review.accepted_applies:
                    try:
                        applied = self.db.apply_board_item_outlook_hints(
                            row["item_id"],
                            actual_due_date=row.get("actual_due_date"),
                            customer_ids=row.get("customer_ids"),
                        )
                        if applied.get("due_date"):
                            due_applied += 1
                        account_applied += int(applied.get("customers") or 0)
                    except Exception:
                        pass
        extra = []
        if due_applied:
            extra.append(f"{due_applied} due date(s) applied")
        if account_applied:
            extra.append(f"{account_applied} account link(s) applied")
        full = msg if not extra else msg.rstrip(".") + "; " + ", ".join(extra) + "."
        self.outlook_status_label.setText(full)
        QMessageBox.information(self, "Outlook import", full)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _load_bid_board_settings(self):
        try:
            roster = self.db.get_estimators_roster(active_only=False)
        except Exception:
            roster = []
        names = [r["name"] for r in roster if r.get("name")]
        extra = self.db.get_all_estimator_names() if hasattr(self.db, "get_all_estimator_names") else []
        combo_names = list(dict.fromkeys(names + extra))

        current = get_current_estimator()
        self.current_estimator_combo.blockSignals(True)
        self.current_estimator_combo.clear()
        self.current_estimator_combo.addItem("")
        for e in combo_names:
            self.current_estimator_combo.addItem(e)
        if current:
            idx = self.current_estimator_combo.findText(current)
            if idx >= 0:
                self.current_estimator_combo.setCurrentIndex(idx)
            else:
                self.current_estimator_combo.setEditText(current)
        self.current_estimator_combo.blockSignals(False)

        self._clear_layout(self.estimator_roster_container)
        if not roster:
            hint = QLabel("No estimators yet. Add one above, or pull names from existing bids.")
            hint.setObjectName("secondaryLabel")
            self.estimator_roster_container.addWidget(hint)
        else:
            for row in roster:
                self.estimator_roster_container.addLayout(self._build_roster_row(row))

        self.board_files_input.setText(get_bid_board_files_path(self.db.db_path))

    def _build_roster_row(self, row):
        eid = row["id"]
        name = row["name"]
        color_hex = row.get("color") or _auto_color_for(name)
        lay = QHBoxLayout()

        name_edit = QLineEdit(name)
        name_edit.setFixedWidth(180)
        lay.addWidget(name_edit)

        swatch = QLabel()
        swatch.setFixedSize(40, 20)
        swatch.setStyleSheet(
            f"background-color: {color_hex}; border: 1px solid #3a3a3a; border-radius: 4px;"
        )
        lay.addWidget(swatch)

        change_btn = QPushButton("Change...")
        change_btn.clicked.connect(
            lambda _, i=eid, n=name_edit, s=swatch: self._on_roster_pick_color(i, n, s)
        )
        lay.addWidget(change_btn)

        rename_btn = QPushButton("Save name")
        rename_btn.clicked.connect(lambda _, i=eid, n=name_edit: self._on_roster_rename(i, n))
        lay.addWidget(rename_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("dangerButton")
        remove_btn.clicked.connect(lambda _, i=eid, n=name: self._on_roster_remove(i, n))
        lay.addWidget(remove_btn)
        lay.addStretch()
        return lay

    def _on_roster_pick_color(self, estimator_id, name_edit, swatch):
        name = name_edit.text().strip()
        start = QColor(swatch.palette().window().color())
        color = QColorDialog.getColor(start, self, f"Color for {name or 'estimator'}")
        if not color.isValid():
            return
        hex_color = color.name()
        try:
            self.db.update_estimator(estimator_id, color=hex_color)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        swatch.setStyleSheet(
            f"background-color: {hex_color}; border: 1px solid #3a3a3a; border-radius: 4px;"
        )
        self.bid_board_status_label.setText(f"Saved color for {name}.")
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")

    def _on_roster_rename(self, estimator_id, name_edit):
        name = name_edit.text().strip()
        try:
            self.db.update_estimator(estimator_id, name=name)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self.bid_board_status_label.setText(f"Saved estimator name: {name}.")
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")
        self._load_bid_board_settings()

    def _on_roster_remove(self, estimator_id, name):
        confirm = QMessageBox.question(
            self, "Remove estimator",
            f"Remove '{name}' from the roster?\nExisting bids keep this name; only the color assignment is removed.",
        )
        if confirm != QMessageBox.Yes:
            return
        self.db.delete_estimator(estimator_id)
        self.bid_board_status_label.setText(f"Removed {name}.")
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")
        self._load_bid_board_settings()

    def _on_add_estimator(self):
        name = self.new_estimator_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Enter an estimator name.")
            return
        try:
            self.db.add_estimator(name)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self.new_estimator_input.clear()
        self.bid_board_status_label.setText(f"Added {name}.")
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")
        self._load_bid_board_settings()

    def _on_pull_estimators(self):
        added = self.db.pull_estimators_from_bids()
        self.bid_board_status_label.setText(
            f"Pulled {added} estimator(s) from existing bids/board items."
            if added else "Roster already includes all known estimators."
        )
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")
        self._load_bid_board_settings()

    def _on_browse_board_files(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Bid Board attachments folder",
            self.board_files_input.text() or os.path.expanduser("~/Dropbox"),
        )
        if path:
            self.board_files_input.setText(path)

    def _on_save_board_files(self):
        path = self.board_files_input.text().strip()
        set_bid_board_files_path(path)
        self.bid_board_status_label.setText("Attachments folder saved.")
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")

    def _on_save_current_estimator(self):
        name = self.current_estimator_combo.currentText().strip()
        set_current_estimator(name)
        if name:
            self.bid_board_status_label.setText(f"'Assign to Me' will assign: {name}.")
        else:
            self.bid_board_status_label.setText("Cleared this PC's estimator identity.")
        self.bid_board_status_label.setStyleSheet("color: #4caf50;")

    def _open_excel_import(self):
        from ui.import_tab import ImportTab

        dlg = QDialog(self)
        dlg.setWindowTitle("Excel Import (legacy)")
        dlg.setMinimumSize(900, 640)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(ImportTab(self.db, dlg))
        close_row = QHBoxLayout()
        close_row.setContentsMargins(16, 8, 16, 12)
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        close_row.addWidget(close_btn)
        lay.addLayout(close_row)
        dlg.exec_()

    def _on_browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Select Database Location",
            self.path_input.text() or os.path.expanduser("~/Dropbox"),
            "SQLite Database (*.db)",
        )
        if path:
            self.path_input.setText(path)

    def _on_save_path(self):
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Error", "Please enter a database path.")
            return
        set_database_path(path)
        self.db.db_path = path
        self.db.init_db()
        self.status_label.setText("Path saved. Restart the app if switching databases.")
        self.status_label.setStyleSheet("color: #4caf50;")

    def _on_test(self):
        path = self.path_input.text().strip()
        if not path:
            self.status_label.setText("No path set.")
            self.status_label.setStyleSheet("color: #f44336;")
            return
        try:
            conn = sqlite3.connect(path, timeout=5)
            conn.execute("SELECT 1")
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            conn.close()
            table_names = [t[0] for t in tables]
            self.status_label.setText(
                f"Connection successful.\n"
                f"Tables found: {', '.join(table_names) if table_names else 'none (new database)'}"
            )
            self.status_label.setStyleSheet("color: #4caf50;")
        except Exception as e:
            self.status_label.setText(f"Connection failed: {e}")
            self.status_label.setStyleSheet("color: #f44336;")

    def _on_rebuild(self):
        try:
            self.db.init_db()
            stats = self.db.get_stats()
            self.rebuild_label.setText(
                f"Rebuild complete. {stats['total']} bids, "
                f"{stats['active']} active, {stats['won']} won."
            )
            self.rebuild_label.setStyleSheet("color: #4caf50;")
        except Exception as e:
            self.rebuild_label.setText(f"Error: {e}")
            self.rebuild_label.setStyleSheet("color: #f44336;")

    def _load_moraware_fields(self):
        cfg = get_config()
        self.mw_url_input.setText(cfg.get("moraware_url", ""))
        self.mw_user_input.setText(cfg.get("moraware_username", ""))
        self.mw_pass_input.setText(cfg.get("moraware_password", ""))
        self.dropbox_path_input.setText(cfg.get("dropbox_bids_path", ""))

    def _on_browse_dropbox(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Dropbox Bids Root Folder",
            self.dropbox_path_input.text() or os.path.expanduser("~/Dropbox"),
        )
        if path:
            self.dropbox_path_input.setText(path)

    def _on_save_dropbox_path(self):
        path = self.dropbox_path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Missing Path", "Please select a Dropbox bids folder path.")
            return
        cfg = get_config()
        cfg["dropbox_bids_path"] = path
        save_config(cfg)
        self.dropbox_status_label.setText("Dropbox bids path saved.")
        self.dropbox_status_label.setStyleSheet("color: #4caf50;")

    # ------------------------------------------------------------------
    # Moraware credentials
    # ------------------------------------------------------------------
    def _on_save_moraware(self):
        url = self.mw_url_input.text().strip()
        user = self.mw_user_input.text().strip()
        pwd = self.mw_pass_input.text().strip()
        if not all([url, user, pwd]):
            QMessageBox.warning(self, "Missing Fields", "Please fill in all Moraware fields.")
            return
        cfg = get_config()
        cfg["moraware_url"] = url
        cfg["moraware_username"] = user
        cfg["moraware_password"] = pwd
        save_config(cfg)
        self.mw_status_label.setText("Credentials saved.")
        self.mw_status_label.setStyleSheet("color: #4caf50;")

    def _on_test_moraware(self):
        url = self.mw_url_input.text().strip()
        user = self.mw_user_input.text().strip()
        pwd = self.mw_pass_input.text().strip()
        if not all([url, user, pwd]):
            self.mw_status_label.setText("Fill in all fields before testing.")
            self.mw_status_label.setStyleSheet("color: #f44336;")
            return
        self.mw_status_label.setText("Connecting...")
        self.mw_status_label.setStyleSheet("color: #999999;")

        self._mw_test_worker = MorewareTestWorker(url, user, pwd)
        self._mw_test_worker.finished.connect(self._on_moraware_test_done)
        self._mw_test_worker.start()

    def _on_moraware_test_done(self, success, message):
        if success:
            self.mw_status_label.setText(f"Connection successful: {message}")
            self.mw_status_label.setStyleSheet("color: #4caf50;")
        else:
            self.mw_status_label.setText(f"Connection failed: {message}")
            self.mw_status_label.setStyleSheet("color: #f44336;")

    def _on_run_diagnostics(self):
        url = self.mw_url_input.text().strip()
        user = self.mw_user_input.text().strip()
        pwd = self.mw_pass_input.text().strip()
        if not all([url, user, pwd]):
            self.mw_status_label.setText("Fill in all fields before running diagnostics.")
            self.mw_status_label.setStyleSheet("color: #f44336;")
            return
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagnostics")
        self.mw_status_label.setText("Running diagnostics...")
        self.mw_status_label.setStyleSheet("color: #999999;")

        self._mw_diag_worker = MorewareDiagWorker(url, user, pwd, output_dir)
        self._mw_diag_worker.finished.connect(self._on_diagnostics_done)
        self._mw_diag_worker.start()

    def _on_diagnostics_done(self, success, message):
        if success:
            self.mw_status_label.setText(message)
            self.mw_status_label.setStyleSheet("color: #4caf50;")
        else:
            self.mw_status_label.setText(f"Diagnostics failed: {message}")
            self.mw_status_label.setStyleSheet("color: #f44336;")

    def refresh(self):
        self.path_input.setText(get_database_path())
        cfg = get_config()
        self.mw_url_input.setText(cfg.get("moraware_url", ""))
        self.mw_user_input.setText(cfg.get("moraware_username", ""))
        self.mw_pass_input.setText(cfg.get("moraware_password", ""))
        self.dropbox_path_input.setText(cfg.get("dropbox_bids_path", ""))
        self._load_bid_board_settings()
