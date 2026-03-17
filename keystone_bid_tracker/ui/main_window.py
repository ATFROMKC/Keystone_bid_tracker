"""
Keystone Bid Tracker - Portal windows
Hub + separate Estimator and PM portal windows.
"""

import os

from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from database import Database
from ui.bids_tab import BidsTab
from ui.customers_tab import CustomersTab
from ui.reports_tab import ReportsTab
from ui.import_tab import ImportTab
from ui.pm_active_jobs_tab import PMActiveJobsTab
from ui.pm_pending_award_tab import PMPendingAwardTab
from ui.pm_history_tab import PMHistoryTab
from ui.settings_tab import SettingsTab

PORTAL_HUB = "hub"
PORTAL_ESTIMATOR = "estimator"
PORTAL_PM = "pm"


def _resolve_logo_path(preferred_path: str = "") -> str:
    """Resolve logo path with user-provided preference, then legacy fallback."""
    candidates = []
    if preferred_path:
        candidates.append(preferred_path)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(project_root, "Assets", "Keystone-Logo-600-DPI.png"))
    candidates.append(os.path.join(project_root, "assets", "Keystone-Logo-600-DPI.png"))

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


class PortalWindowBase(QMainWindow):
    def __init__(self, db: Database, title: str, logo_path: str = ""):
        super().__init__()
        self.db = db
        self._logo_path = logo_path
        self.setWindowTitle(title)
        self.setMinimumSize(1200, 700)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def _build_header(self, title: str, subtitle: str = "", right_widget: QWidget = None) -> QWidget:
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(16, 12, 16, 8)
        row.setSpacing(12)

        logo_label = QLabel()
        logo_file = _resolve_logo_path(self._logo_path)
        if logo_file:
            pixmap = QPixmap(logo_file)
            if not pixmap.isNull():
                logo_label.setPixmap(pixmap.scaledToHeight(42, Qt.SmoothTransformation))
        row.addWidget(logo_label)

        text_col = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("headingLabel")
        text_col.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("secondaryLabel")
            text_col.addWidget(subtitle_label)
        row.addLayout(text_col)
        row.addStretch()
        if right_widget is not None:
            row.addWidget(right_widget)
        return header

    def _on_tab_changed(self, index: int):
        widget = self.tabs.widget(index)
        if hasattr(widget, "refresh"):
            widget.refresh()


class HubWindow(PortalWindowBase):
    def __init__(self, db: Database, open_estimator_cb, open_pm_cb, logo_path: str = ""):
        super().__init__(db, "Keystone Hub", logo_path=logo_path)
        self._open_estimator_cb = open_estimator_cb
        self._open_pm_cb = open_pm_cb
        self._build_ui()

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_bar = QWidget()
        button_row = QHBoxLayout(button_bar)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        estimator_btn = QPushButton("Enter Estimator Portal")
        estimator_btn.setObjectName("primaryButton")
        estimator_btn.clicked.connect(self._open_estimator_cb)
        pm_btn = QPushButton("Enter PM Portal")
        pm_btn.clicked.connect(self._open_pm_cb)
        button_row.addWidget(estimator_btn)
        button_row.addWidget(pm_btn)
        header = self._build_header("Main Hub", "Accounts and Settings", right_widget=button_bar)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.customers_tab = CustomersTab(self.db, self)
        self.settings_tab = SettingsTab(self.db, self)
        self.tabs.addTab(self.customers_tab, "Accounts")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        self.setCentralWidget(container)


class EstimatorWindow(PortalWindowBase):
    def __init__(self, db: Database, open_hub_cb, logo_path: str = ""):
        super().__init__(db, "Estimator Portal", logo_path=logo_path)
        self._open_hub_cb = open_hub_cb
        self._build_ui()

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        back_btn = QPushButton("Back to Hub")
        back_btn.clicked.connect(self._open_hub_cb)
        layout.addWidget(self._build_header("Estimator Portal", "Bids, Import, and Reports", right_widget=back_btn))

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.bids_tab = BidsTab(self.db, self)
        self.import_tab = ImportTab(self.db, self)
        self.reports_tab = ReportsTab(self.db, self)
        self.tabs.addTab(self.bids_tab, "Bids")
        self.tabs.addTab(self.import_tab, "Import")
        self.tabs.addTab(self.reports_tab, "Reports")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        self.setCentralWidget(container)


class PMWindow(PortalWindowBase):
    def __init__(self, db: Database, open_hub_cb, logo_path: str = ""):
        super().__init__(db, "PM Portal", logo_path=logo_path)
        self._open_hub_cb = open_hub_cb
        self.active_jobs_session_cache = {
            "jobs": [],
            "fetched_at": "",
        }
        self._build_ui()

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        back_btn = QPushButton("Back to Hub")
        back_btn.clicked.connect(self._open_hub_cb)
        layout.addWidget(self._build_header("PM Portal", "Active Jobs, Pending Award, and History", right_widget=back_btn))

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.active_jobs_tab = PMActiveJobsTab(self.db, self.active_jobs_session_cache, self)
        self.pending_award_tab = PMPendingAwardTab(self.db, self)
        self.history_tab = PMHistoryTab(self.db, self)
        self.tabs.addTab(self.active_jobs_tab, "Active Jobs")
        self.tabs.addTab(self.pending_award_tab, "Pending Award")
        self.tabs.addTab(self.history_tab, "Completed History")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        self.setCentralWidget(container)
