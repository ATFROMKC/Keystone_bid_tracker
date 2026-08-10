"""
Read-only Classic Outlook (COM) calendar client.

Never writes to Outlook: do not call Save / Delete / Move / Send, and do not
assign appointment properties. Returns plain Python dicts only — no COM objects.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta

from utils.outlook_graph_client import CENTRAL_TZ

logger = logging.getLogger(__name__)

OL_FOLDER_CALENDAR = 9
OL_APPOINTMENT_ITEM = 1
OL_MODULE_CALENDAR = 1
OL_APPOINTMENT_CLASS = 26

CALENDAR_ID_PREFIX = "com:"
MAX_EVENTS_PER_SYNC = 8000
BODY_FETCH_TIMEOUT_SEC = 50
BODY_MAX_CHARS = 1200


class OutlookComError(Exception):
    """Classic Outlook is missing, busy, or the selected folder cannot be read."""


def parse_desktop_calendar_id(calendar_id: str) -> str:
    cid = (calendar_id or "").strip()
    if cid.startswith(CALENDAR_ID_PREFIX):
        return cid[len(CALENDAR_ID_PREFIX):]
    return cid


def desktop_calendar_id(folder_entry_id: str) -> str:
    eid = (folder_entry_id or "").strip()
    if not eid:
        return ""
    if eid.startswith(CALENDAR_ID_PREFIX):
        return eid
    return CALENDAR_ID_PREFIX + eid


def parse_outlook_categories(raw) -> list:
    """Outlook Categories is a comma-separated string, not a list."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(c).strip() for c in raw if str(c).strip()]
    text = str(raw).strip()
    if not text:
        return []
    return [p.strip() for p in text.split(",") if p.strip()]


def _require_win32():
    try:
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401
    except ImportError as e:
        raise OutlookComError(
            "The 'pywin32' package is not installed. "
            "Run: .venv\\Scripts\\python.exe -m pip install pywin32"
        ) from e


def _as_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime(
            int(value.year), int(value.month), int(value.day),
            int(getattr(value, "hour", 0) or 0),
            int(getattr(value, "minute", 0) or 0),
            int(getattr(value, "second", 0) or 0),
        )
    except Exception:
        return None


def _board_start_iso(start_val, is_all_day: bool) -> str:
    dt = _as_datetime(start_val)
    if dt is None:
        return ""
    if is_all_day:
        return date(dt.year, dt.month, dt.day).isoformat()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CENTRAL_TZ)
    else:
        dt = dt.astimezone(CENTRAL_TZ)
    return dt.isoformat()


def _safe_str(getter, default=""):
    try:
        val = getter()
        if val is None:
            return default
        return str(val)
    except Exception:
        return default


def _folder_record(folder, store_name="", nav_group=""):
    name = _safe_str(lambda: folder.Name)
    path = _safe_str(lambda: folder.FolderPath)
    entry_id = _safe_str(lambda: folder.EntryID)
    store_id = ""
    try:
        store = folder.Store
        store_name = store_name or _safe_str(lambda: store.DisplayName)
        store_id = _safe_str(lambda: store.StoreID)
    except Exception:
        pass
    return {
        "id": desktop_calendar_id(entry_id),
        "name": name or "(unnamed)",
        "path": path,
        "store_id": store_id,
        "owner": {"name": store_name or "", "address": ""},
        "nav_group": nav_group or "",
        "isShared": (nav_group or "").lower().find("shared") >= 0,
    }


class OutlookDesktopClient:
    """Attach to the current Classic Outlook profile and read calendars."""

    def __init__(self, store_id: str = ""):
        self._store_id = (store_id or "").strip()
        self._app = None
        self._ns = None

    def connect(self):
        _require_win32()
        import pythoncom
        import win32com.client

        try:
            pythoncom.CoInitialize()
        except Exception:
            pass
        try:
            self._app = win32com.client.GetActiveObject("Outlook.Application")
        except Exception as active_err:
            try:
                self._app = win32com.client.Dispatch("Outlook.Application")
            except Exception as dispatch_err:
                raise OutlookComError(
                    "Could not connect to Classic Outlook. Open Classic Outlook "
                    "(not the new Outlook app) and sign in, then try again.\n"
                    f"Details: {dispatch_err}"
                ) from dispatch_err
            logger.info("Outlook COM Dispatch after GetActiveObject failed: %s", active_err)
        try:
            self._ns = self._app.GetNamespace("MAPI")
        except Exception as e:
            raise OutlookComError(
                f"Outlook is installed but MAPI could not be opened: {e}"
            ) from e
        return self

    def _namespace(self):
        if self._ns is None:
            self.connect()
        return self._ns

    def _application(self):
        if self._app is None:
            self.connect()
        return self._app

    def list_calendars(self) -> list:
        ns = self._namespace()
        by_id = {}

        def _add(rec):
            cid = rec.get("id") or ""
            if not cid:
                return
            prev = by_id.get(cid)
            if prev is None:
                by_id[cid] = rec
                return
            if rec.get("nav_group") and not prev.get("nav_group"):
                prev["nav_group"] = rec["nav_group"]
                prev["isShared"] = rec.get("isShared") or prev.get("isShared")

        for rec in self._calendars_from_nav_pane():
            _add(rec)
        for rec in self._calendars_from_stores(ns):
            _add(rec)
        rows = list(by_id.values())
        rows.sort(key=lambda r: (
            0 if r.get("isShared") else 1,
            (r.get("name") or "").lower(),
            r.get("path") or "",
        ))
        return rows

    def _calendars_from_nav_pane(self) -> list:
        found = []
        try:
            explorer = self._application().ActiveExplorer()
            if explorer is None:
                return found
            module = explorer.NavigationPane.Modules.GetNavigationModule(OL_MODULE_CALENDAR)
            groups = module.NavigationGroups
            for gi in range(1, groups.Count + 1):
                group = groups.Item(gi)
                gname = _safe_str(lambda g=group: g.Name)
                nav_folders = group.NavigationFolders
                for fi in range(1, nav_folders.Count + 1):
                    try:
                        folder = nav_folders.Item(fi).Folder
                    except Exception:
                        continue
                    found.append(_folder_record(folder, nav_group=gname))
        except Exception as exc:
            logger.warning("Outlook nav pane calendar list failed: %s", exc)
        return found

    def _calendars_from_stores(self, ns) -> list:
        found = []
        try:
            stores = ns.Stores
        except Exception as exc:
            logger.warning("Outlook store list failed: %s", exc)
            return found
        for i in range(1, stores.Count + 1):
            try:
                store = stores.Item(i)
                sname = _safe_str(lambda s=store: s.DisplayName)
                root = store.GetRootFolder()
            except Exception:
                continue
            self._walk_appointment_folders(root, sname, found, 0)
        return found

    def _walk_appointment_folders(self, folder, store_name, found, depth, max_depth=6):
        if depth > max_depth:
            return
        try:
            item_type = folder.DefaultItemType
        except Exception:
            item_type = None
        if item_type in (OL_FOLDER_CALENDAR, OL_APPOINTMENT_ITEM):
            found.append(_folder_record(folder, store_name=store_name))
        try:
            subs = folder.Folders
            count = int(subs.Count)
        except Exception:
            return
        for i in range(1, count + 1):
            try:
                child = subs.Item(i)
            except Exception:
                continue
            self._walk_appointment_folders(child, store_name, found, depth + 1, max_depth)

    def _get_folder(self, calendar_id: str, store_id: str = ""):
        ns = self._namespace()
        entry_id = parse_desktop_calendar_id(calendar_id)
        if not entry_id:
            raise OutlookComError("No Outlook calendar is selected.")
        sid = (store_id or self._store_id or "").strip()
        try:
            if sid:
                return ns.GetFolderFromID(entry_id, sid)
            return ns.GetFolderFromID(entry_id)
        except Exception as e:
            if sid:
                try:
                    return ns.GetFolderFromID(entry_id)
                except Exception:
                    pass
            raise OutlookComError(
                "The selected Outlook calendar could not be opened. "
                "Refresh calendars in Settings and pick Commercial Bid again.\n"
                f"Details: {e}"
            ) from e

    def list_calendar_view(self, calendar_id: str, start_d: date, end_d: date, store_id: str = ""):
        folder = self._get_folder(calendar_id, store_id=store_id)
        cid = desktop_calendar_id(parse_desktop_calendar_id(calendar_id))
        # Items.Restrict / IncludeRecurrences / GetTable+EntryID hang or omit IDs on this
        # ~6k-item shared calendar. A linear read-only walk is ~15s and yields EntryIDs.
        try:
            items = folder.Items
            item = items.GetFirst()
        except Exception as e:
            raise OutlookComError(f"Could not read appointments from the Outlook folder: {e}") from e

        events = []
        scanned = 0
        while item is not None and len(events) < MAX_EVENTS_PER_SYNC:
            scanned += 1
            try:
                cls = item.Class
            except Exception:
                cls = None
            if cls == OL_APPOINTMENT_CLASS:
                start_val = _safe_raw(lambda: item.Start)
                dt = _as_datetime(start_val)
                item_day = date(dt.year, dt.month, dt.day) if dt else None
                if item_day is not None and start_d <= item_day <= end_d:
                    try:
                        cancelled = bool(int(item.MeetingStatus or 0) == 5)
                    except Exception:
                        cancelled = False
                    try:
                        is_all_day = bool(item.AllDayEvent)
                    except Exception:
                        is_all_day = False
                    events.append({
                        "source_event_id": _safe_str(lambda: item.EntryID),
                        "source_calendar_id": cid,
                        "subject": _safe_str(lambda: item.Subject) or "(No subject)",
                        "start": _board_start_iso(start_val, is_all_day),
                        "end": _board_start_iso(_safe_raw(lambda: item.End), is_all_day),
                        "is_all_day": is_all_day,
                        "is_cancelled": cancelled,
                        "categories": parse_outlook_categories(_safe_raw(lambda: item.Categories)),
                        "location": _safe_str(lambda: item.Location).strip(),
                        "body": "",
                        "last_modified": _safe_str(lambda: item.LastModificationTime),
                    })
            try:
                item = items.GetNext()
            except Exception:
                break
        logger.info("Outlook desktop walk scanned %s item(s), kept %s", scanned, len(events))
        return events

    def enrich_event_bodies(self, events: list, timeout_sec: int = BODY_FETCH_TIMEOUT_SEC) -> dict:
        """Fill event['body'] via a killable subprocess.

        Returns {"filled": int, "attempted": int, "timed_out": bool}.
        """
        import json
        import subprocess
        import sys

        empty = {"filled": 0, "attempted": 0, "timed_out": False}
        if not events:
            return empty
        eids = [e.get("source_event_id") for e in events if e.get("source_event_id")]
        if not eids:
            return empty
        worker = os.path.join(os.path.dirname(__file__), "outlook_body_fetch_worker.py")
        if not os.path.isfile(worker):
            logger.warning("Body fetch worker missing: %s", worker)
            return empty
        filled = 0
        timed_out = False
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", worker],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            logger.warning("Could not start Outlook body worker: %s", e)
            return empty
        try:
            out, err = proc.communicate(json.dumps(eids), timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            out, err = proc.communicate()
            logger.warning(
                "Outlook body fetch timed out after %ss (Trust Center may be blocking). "
                "Continuing with Subject/Location only.",
                timeout_sec,
            )
        by_id = {}
        for line in (out or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            eid = rec.get("id")
            if eid and rec.get("ok"):
                by_id[eid] = (rec.get("body") or "")[:BODY_MAX_CHARS]
        for ev in events:
            eid = ev.get("source_event_id")
            if eid in by_id and by_id[eid]:
                ev["body"] = by_id[eid]
                filled += 1
        if err and not filled:
            logger.info("Outlook body worker stderr: %s", (err or "")[:300])
        return {"filled": filled, "attempted": len(eids), "timed_out": timed_out}

    def test_calendar_read(self, calendar_id: str, store_id: str = ""):
        today = date.today()
        events = self.list_calendar_view(
            calendar_id, today, today + timedelta(days=7), store_id=store_id
        )
        user = "Classic Outlook"
        try:
            user = _safe_str(lambda: self._namespace().CurrentUser.Name) or user
        except Exception:
            pass
        return {"user": user, "event_count": len(events)}


def _safe_raw(getter, default=None):
    try:
        return getter()
    except Exception:
        return default
