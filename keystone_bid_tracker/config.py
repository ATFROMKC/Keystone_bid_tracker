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


# ----------------------------------------------------------------------
# Bid Board (Calendar) presentation settings
# ----------------------------------------------------------------------

# Universal color for completed board cards (blue), and gray for unassigned.
DEFAULT_COMPLETE_BLUE = "#4a9eff"
UNASSIGNED_GRAY = "#6b6b6b"
NOT_BIDDING_COLOR = "#8a5a3a"

# Palette used to auto-assign a stable color to each assigned estimator.
ESTIMATOR_COLOR_PALETTE = [
    "#4caf50",  # green
    "#ff9800",  # orange
    "#e91e63",  # pink
    "#9c27b0",  # purple
    "#00bcd4",  # cyan
    "#ffc107",  # amber
    "#8bc34a",  # light green
    "#ff5722",  # deep orange
    "#795548",  # brown
    "#607d8b",  # blue gray
]


def get_estimator_colors() -> dict:
    """Return the user-configured {estimator_name: hex_color} overrides."""
    cfg = get_config()
    colors = cfg.get("estimator_colors")
    return dict(colors) if isinstance(colors, dict) else {}


def set_estimator_colors(colors: dict):
    cfg = get_config()
    cfg["estimator_colors"] = dict(colors or {})
    save_config(cfg)


def _auto_color_for(name: str) -> str:
    """Deterministic palette color for an estimator name (stable across runs)."""
    if not name:
        return UNASSIGNED_GRAY
    idx = sum(ord(ch) for ch in name) % len(ESTIMATOR_COLOR_PALETTE)
    return ESTIMATOR_COLOR_PALETTE[idx]


def get_estimator_color(name: str) -> str:
    """Resolve an estimator's card color: explicit override, else auto palette."""
    if not name or not str(name).strip():
        return UNASSIGNED_GRAY
    name = str(name).strip()
    overrides = get_estimator_colors()
    if name in overrides and overrides[name]:
        return overrides[name]
    return _auto_color_for(name)


def get_complete_blue() -> str:
    cfg = get_config()
    val = (cfg.get("complete_blue") or "").strip()
    return val or DEFAULT_COMPLETE_BLUE


def set_complete_blue(hex_color: str):
    cfg = get_config()
    cfg["complete_blue"] = (hex_color or "").strip() or DEFAULT_COMPLETE_BLUE
    save_config(cfg)


def get_current_estimator() -> str:
    """This machine's estimator identity for the 'Assign to Me' action.

    Empty string means unset (the app has no login/user identity, so this is an
    explicit opt-in setting rather than an invented identity).
    """
    cfg = get_config()
    return (cfg.get("current_estimator") or "").strip()


def set_current_estimator(name: str):
    cfg = get_config()
    cfg["current_estimator"] = (name or "").strip()
    save_config(cfg)


def get_bid_board_files_path(db_path: str = "") -> str:
    """Folder used to store copied Bid Board attachments.

    Defaults to <db_dir>/BidBoardFiles so Dropbox-synced DBs share files.
    """
    cfg = get_config()
    override = (cfg.get("bid_board_files_path") or "").strip()
    if override:
        return override
    base = os.path.dirname(db_path) if db_path else _get_app_dir()
    return os.path.join(base, "BidBoardFiles")


def set_bid_board_files_path(path: str):
    cfg = get_config()
    cfg["bid_board_files_path"] = (path or "").strip()
    save_config(cfg)


def get_calendar_view(default: str = "month") -> str:
    cfg = get_config()
    view = (cfg.get("calendar_view") or "").strip().lower()
    if view in ("month", "3week", "week", "day"):
        return view
    return default


def set_calendar_view(view: str):
    view = (view or "").strip().lower()
    if view not in ("month", "3week", "week", "day"):
        return
    cfg = get_config()
    cfg["calendar_view"] = view
    save_config(cfg)


def get_hide_weekends(default: bool = False) -> bool:
    cfg = get_config()
    val = cfg.get("hide_weekends")
    if isinstance(val, bool):
        return val
    return default


def set_hide_weekends(hide: bool):
    cfg = get_config()
    cfg["hide_weekends"] = bool(hide)
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


# ----------------------------------------------------------------------
# Outlook → Bid Board (read-only sync). Local config only — not secrets in git.
# ----------------------------------------------------------------------

DEFAULT_OUTLOOK_LOOKBACK_DAYS = 60
DEFAULT_OUTLOOK_LOOKAHEAD_DAYS = 120

DEFAULT_OUTLOOK_CATEGORY_MAP = {
    "complete_names": ["Complete", "Completed"],
    "not_bidding_names": ["Not Bidding", "No Scope"],
    # Optional explicit overrides, e.g. {"Scott Complete": "Scott"}.
    # Patterns "Name in Progress" and "Name Complete" are also recognized.
    "estimator_in_progress": {},
}


def get_outlook_sync_config() -> dict:
    cfg = get_config()
    raw = cfg.get("outlook_sync")
    data = dict(raw) if isinstance(raw, dict) else {}
    cmap = data.get("category_map")
    if not isinstance(cmap, dict):
        cmap = {}
    merged_map = {
        "complete_names": list(cmap.get("complete_names") or DEFAULT_OUTLOOK_CATEGORY_MAP["complete_names"]),
        "not_bidding_names": list(
            cmap.get("not_bidding_names") or DEFAULT_OUTLOOK_CATEGORY_MAP["not_bidding_names"]
        ),
        "estimator_in_progress": dict(cmap.get("estimator_in_progress") or {}),
    }
    try:
        lookback = int(data.get("lookback_days") if data.get("lookback_days") is not None else DEFAULT_OUTLOOK_LOOKBACK_DAYS)
    except (TypeError, ValueError):
        lookback = DEFAULT_OUTLOOK_LOOKBACK_DAYS
    try:
        lookahead = int(data.get("lookahead_days") or DEFAULT_OUTLOOK_LOOKAHEAD_DAYS)
    except (TypeError, ValueError):
        lookahead = DEFAULT_OUTLOOK_LOOKAHEAD_DAYS
    provider = (data.get("provider") or "desktop").strip().lower()
    if provider not in ("desktop", "graph"):
        provider = "desktop"
    sync_window = (data.get("sync_window") or "week_onward").strip().lower()
    if sync_window not in ("week_onward", "rolling"):
        sync_window = "week_onward"
    return {
        "provider": provider,
        "sync_window": sync_window,
        "read_appointment_bodies": bool(data.get("read_appointment_bodies", True)),
        "client_id": (data.get("client_id") or "").strip(),
        "tenant_id": (data.get("tenant_id") or "").strip(),
        "calendar_id": (data.get("calendar_id") or "").strip(),
        "calendar_name": (data.get("calendar_name") or "").strip(),
        "calendar_owner": (data.get("calendar_owner") or "").strip(),
        "calendar_store_id": (data.get("calendar_store_id") or "").strip(),
        "calendar_path": (data.get("calendar_path") or "").strip(),
        "lookback_days": max(0, lookback),
        "lookahead_days": max(1, lookahead),
        "last_synced_at": (data.get("last_synced_at") or "").strip(),
        "category_map": merged_map,
    }


def save_outlook_sync_config(updates: dict):
    cfg = get_config()
    current = get_outlook_sync_config()
    current.update(updates or {})
    cfg["outlook_sync"] = current
    save_config(cfg)
