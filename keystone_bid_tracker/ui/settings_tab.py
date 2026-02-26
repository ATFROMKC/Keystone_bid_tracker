"""
Keystone Bid Tracker - Settings Tab
Database path config, test connection, version info, rebuild stats.
"""

import os
import sqlite3

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from config import get_config, save_config, get_database_path, set_database_path


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
