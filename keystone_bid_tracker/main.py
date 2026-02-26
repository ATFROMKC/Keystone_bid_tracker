"""
Keystone Bid Tracker - Entry Point
"""

import sys
import os
import logging

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

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

    def show_hub(self):
        self._hide_all()
        self.hub_window.show()
        self.hub_window.raise_()
        self.hub_window.activateWindow()

    def show_estimator(self):
        set_last_portal(PORTAL_ESTIMATOR)
        self._hide_all()
        self.estimator_window.show()
        self.estimator_window.raise_()
        self.estimator_window.activateWindow()

    def show_pm(self):
        set_last_portal(PORTAL_PM)
        self._hide_all()
        self.pm_window.show()
        self.pm_window.raise_()
        self.pm_window.activateWindow()

    def show_startup_window(self):
        last_portal = get_last_portal(default=PORTAL_HUB)
        if last_portal == PORTAL_ESTIMATOR:
            self.show_estimator()
        elif last_portal == PORTAL_PM:
            self.show_pm()
        else:
            self.show_hub()


def main():

    app = QApplication(sys.argv)
    app.setApplicationName("Keystone Bid Tracker")
    app.setApplicationVersion(APP_VERSION)

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
