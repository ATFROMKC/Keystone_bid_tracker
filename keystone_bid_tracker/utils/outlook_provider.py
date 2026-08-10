"""
Factory for read-only Outlook event providers (Classic desktop COM or Graph).

CalendarTab and workers should call get_outlook_provider() — never import COM
or Graph clients directly from UI code (except Graph sign-in, which is Graph-only).
"""

from __future__ import annotations

from datetime import date

from config import get_outlook_sync_config


def normalize_provider_name(value) -> str:
    name = (value or "desktop").strip().lower()
    if name in ("desktop", "local", "com", "outlook_desktop"):
        return "desktop"
    if name in ("graph", "microsoft_graph", "msgraph"):
        return "graph"
    return "desktop"


def graph_event_to_neutral(ev: dict, calendar_id: str) -> dict:
    """Map a Graph calendarView event into the shared sync shape."""
    start = ev.get("start") or {}
    end = ev.get("end") or {}
    loc = ev.get("location") or {}
    if isinstance(loc, dict):
        location = (loc.get("displayName") or "").strip()
    else:
        location = str(loc or "").strip()
    is_all_day = bool(ev.get("isAllDay"))
    if is_all_day:
        start_s = (start.get("date") or start.get("dateTime") or "")[:10]
        end_s = (end.get("date") or end.get("dateTime") or "")[:10]
    else:
        start_s = (start.get("dateTime") or start.get("date") or "")
        end_s = (end.get("dateTime") or end.get("date") or "")
    cats = ev.get("categories") or []
    if isinstance(cats, str):
        cats = [p.strip() for p in cats.split(",") if p.strip()]
    return {
        "source_event_id": (ev.get("id") or "").strip(),
        "source_calendar_id": calendar_id,
        "subject": ev.get("subject") or "(No subject)",
        "start": start_s,
        "end": end_s,
        "is_all_day": is_all_day,
        "is_cancelled": bool(ev.get("isCancelled")),
        "categories": cats,
        "location": location,
        "body": (ev.get("bodyPreview") or "").strip(),
        "last_modified": ev.get("lastModifiedDateTime") or "",
    }


class OutlookGraphProvider:
    def __init__(self, cfg: dict):
        from utils.outlook_graph_client import OutlookGraphClient

        self.cfg = cfg
        self.client = OutlookGraphClient(cfg.get("tenant_id") or "", cfg.get("client_id") or "")
        self.client.acquire_token(interactive=False)

    def list_calendars(self):
        return self.client.list_calendars()

    def list_events(self, calendar_id: str, start_d: date, end_d: date):
        raw = self.client.list_calendar_view(calendar_id, start_d, end_d)
        events = [graph_event_to_neutral(ev, calendar_id) for ev in raw]
        filled = sum(1 for e in events if (e.get("body") or "").strip())
        self.body_stats = {
            "filled": filled,
            "attempted": len(events),
            "timed_out": False,
            "source": "preview",
        }
        return events

    def test_calendar_read(self, calendar_id: str):
        return self.client.test_calendar_read(calendar_id)


class OutlookDesktopProvider:
    def __init__(self, cfg: dict):
        from utils.outlook_com_client import OutlookDesktopClient

        self.cfg = cfg
        self.client = OutlookDesktopClient(store_id=cfg.get("calendar_store_id") or "")
        self.client.connect()

    def list_calendars(self):
        return self.client.list_calendars()

    def list_events(self, calendar_id: str, start_d: date, end_d: date):
        events = self.client.list_calendar_view(
            calendar_id,
            start_d,
            end_d,
            store_id=self.cfg.get("calendar_store_id") or "",
        )
        self.body_stats = {
            "filled": 0,
            "attempted": len(events),
            "timed_out": False,
            "source": "desktop",
        }
        if self.cfg.get("read_appointment_bodies", True):
            try:
                stats = self.client.enrich_event_bodies(events) or {}
                self.body_stats = {
                    "filled": int(stats.get("filled") or 0),
                    "attempted": int(stats.get("attempted") or len(events)),
                    "timed_out": bool(stats.get("timed_out")),
                    "source": "desktop",
                }
            except Exception:
                self.body_stats["filled"] = 0
        return events

    def test_calendar_read(self, calendar_id: str):
        info = self.client.test_calendar_read(
            calendar_id, store_id=self.cfg.get("calendar_store_id") or ""
        )
        return info


def get_outlook_provider(cfg: dict = None):
    cfg = cfg if cfg is not None else get_outlook_sync_config()
    if normalize_provider_name(cfg.get("provider")) == "graph":
        return OutlookGraphProvider(cfg)
    return OutlookDesktopProvider(cfg)


def provider_display_name(cfg: dict = None) -> str:
    cfg = cfg if cfg is not None else get_outlook_sync_config()
    if normalize_provider_name(cfg.get("provider")) == "graph":
        return "Microsoft Graph"
    return "Local Outlook Desktop"
