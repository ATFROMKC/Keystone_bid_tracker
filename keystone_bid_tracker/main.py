"""
Keystone Bid Tracker - Entry Point
"""

import sys
import os
import logging

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Ensure package imports work when running from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from styles.theme import apply_theme
from config import get_database_path, set_database_path, get_config, get_last_portal, set_last_portal
from database import Database
from ui.main_window import (
    HubWindow,
    EstimatorWindow,
    PMWindow,
    PORTAL_HUB,
    PORTAL_ESTIMATOR,
    PORTAL_PM,
)

APP_VERSION = "1.0.0"
LOGGER = logging.getLogger(__name__)


def _base_dir() -> str:
    """Return the runtime base directory (supports frozen builds)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _asset_path(*parts: str) -> str:
    return os.path.join(_base_dir(), "Assets", *parts)


def _apply_windows_taskbar_identity() -> None:
    """Windows: taskbar/pin uses Bid Tracker icon instead of generic Python (before UI)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Keystone.BidTracker.App.1.0"
        )
    except Exception:
        LOGGER.debug("Could not set Windows AppUserModelID", exc_info=True)


def _apply_app_icon(app: QApplication) -> None:
    """Apply the app icon when asset files are available."""
    icon_path = _asset_path("icons", "bidtracker.ico")
    if not os.path.exists(icon_path):
        LOGGER.warning("App icon not found at: %s", icon_path)
        return

    icon = QIcon(icon_path)
    if icon.isNull():
        LOGGER.warning("App icon failed to load from: %s", icon_path)
        return

    app.setWindowIcon(icon)


def prompt_for_db_path(app: QApplication) -> str:
    """Show a dialog asking the user to choose a database file location."""
    msg = QMessageBox()
    msg.setWindowTitle("Keystone Bid Tracker - Setup")
    msg.setText(
        "No database configured.\n\n"
        "Select an existing .db file or choose a location to create a new one.\n"
        "This should be inside your shared Dropbox folder."
    )
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setDefaultButton(QMessageBox.Ok)
    result = msg.exec_()

    if result == QMessageBox.Cancel:
        return ""

    path, _ = QFileDialog.getSaveFileName(
        None,
        "Select Database Location",
        os.path.expanduser("~/Dropbox"),
        "SQLite Database (*.db)",
    )
    return path


class PortalController:
    def __init__(self, db: Database):
        self.db = db
        cfg = get_config()
        self.logo_path = (cfg.get("portal_logo_path") or "").strip()

        self.hub_window = HubWindow(
            self.db,
            open_estimator_cb=self.show_estimator,
            open_pm_cb=self.show_pm,
            logo_path=self.logo_path,
        )
        self.estimator_window = EstimatorWindow(
            self.db,
            open_hub_cb=self.show_hub,
            logo_path=self.logo_path,
        )
        self.pm_window = PMWindow(
            self.db,
            open_hub_cb=self.show_hub,
            logo_path=self.logo_path,
        )

    def _hide_all(self):
        self.hub_window.hide()
        self.estimator_window.hide()
        self.pm_window.hide()

    def _current_window(self):
        for window in (self.hub_window, self.estimator_window, self.pm_window):
            if window.isVisible():
                return window
        return None

    def _switch_to(self, target_window, portal_key=None):
        if portal_key:
            set_last_portal(portal_key)

        source_window = self._current_window()
        source_is_maximized = bool(source_window and source_window.isMaximized())
        source_geometry = None
        if source_window and not source_is_maximized:
            source_geometry = source_window.geometry()

        self._hide_all()

        if source_window is None:
            # Startup path: preserve target's own previous state when possible.
            if target_window.isMaximized():
                target_window.showMaximized()
            else:
                target_window.show()
        elif source_is_maximized:
            target_window.showMaximized()
        else:
            if source_geometry is not None:
                target_window.setGeometry(source_geometry)
            target_window.showNormal()

        target_window.raise_()
        target_window.activateWindow()

    def show_hub(self):
        self._switch_to(self.hub_window)

    def show_estimator(self):
        self._switch_to(self.estimator_window, PORTAL_ESTIMATOR)

    def show_pm(self):
        self._switch_to(self.pm_window, PORTAL_PM)

    def show_startup_window(self):
        last_portal = get_last_portal(default=PORTAL_HUB)
        if last_portal == PORTAL_ESTIMATOR:
            self.show_estimator()
        elif last_portal == PORTAL_PM:
            self.show_pm()
        else:
            self.show_hub()


def main():

    _apply_windows_taskbar_identity()
    app = QApplication(sys.argv)
    app.setApplicationName("Keystone Bid Tracker")
    app.setApplicationVersion(APP_VERSION)
    _apply_app_icon(app)

    apply_theme(app)

    db_path = get_database_path()

    if not db_path:
        db_path = prompt_for_db_path(app)
        if not db_path:
            sys.exit(0)
        set_database_path(db_path)

    db = Database(db_path)
    db.init_db()

    controller = PortalController(db)
    app._portal_controller = controller
    controller.show_startup_window()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
