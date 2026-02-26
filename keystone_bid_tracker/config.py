"""
Keystone Bid Tracker - Configuration
Reads/writes config.json next to the executable (or script).
"""

import json
import os
import sys
from datetime import date


def _get_app_dir() -> str:
    """Return the directory where config.json lives (next to .exe or script)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path() -> str:
    return os.path.join(_get_app_dir(), "config.json")


def get_config() -> dict:
    path = get_config_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    config["last_opened"] = date.today().isoformat()
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_database_path() -> str:
    """Return the configured database path, or empty string if not set."""
    cfg = get_config()
    return cfg.get("database_path", "")


def set_database_path(db_path: str):
    cfg = get_config()
    cfg["database_path"] = db_path
    save_config(cfg)


def get_last_portal(default: str = "hub") -> str:
    cfg = get_config()
    portal = (cfg.get("last_portal") or "").strip().lower()
    if portal in ("hub", "estimator", "pm"):
        return portal
    return default


def set_last_portal(portal: str):
    portal = (portal or "").strip().lower()
    if portal not in ("hub", "estimator", "pm"):
        return
    cfg = get_config()
    cfg["last_portal"] = portal
    save_config(cfg)
