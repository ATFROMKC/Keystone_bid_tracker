"""
Read-only Microsoft Graph calendar client.

This module must never issue Outlook/Graph write calls (no POST/PATCH/DELETE
to calendar endpoints). Authentication is delegated MSAL public-client only.
"""

import json
import os
import logging
from datetime import date, datetime, time, timedelta, tzinfo
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from config import _get_app_dir

logger = logging.getLogger(__name__)

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
# Windows / Graph timezone name (covers CST/CDT). Used in Prefer: outlook.timezone.
GRAPH_OUTLOOK_TZ = "Central Standard Time"


class _UsCentralFallback(tzinfo):
    """CST/CDT when the tzdata package is not installed (common on Windows)."""

    def utcoffset(self, dt):
        return timedelta(hours=-5 if self._is_dst(dt) else -6)

    def dst(self, dt):
        return timedelta(hours=1) if self._is_dst(dt) else timedelta(0)

    def tzname(self, dt):
        return "CDT" if self._is_dst(dt) else "CST"

    @staticmethod
    def _is_dst(dt):
        if dt is None:
            return False
        year = dt.year
        march1 = date(year, 3, 1)
        dst_start = datetime(year, 3, 1 + (6 - march1.weekday()) % 7 + 7, 2, 0)
        nov1 = date(year, 11, 1)
        dst_end = datetime(year, 11, 1 + (6 - nov1.weekday()) % 7, 2, 0)
        naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
        return dst_start <= naive < dst_end


def _central_tz():
    try:
        return ZoneInfo("America/Chicago")
    except ZoneInfoNotFoundError:
        logger.warning("tzdata not installed; using built-in US Central fallback")
        return _UsCentralFallback()


CENTRAL_TZ = _central_tz()
READ_SCOPES = ["User.Read", "Calendars.Read.Shared"]
TOKEN_CACHE_NAME = "msal_token_cache.bin"

CONSENT_HINT = (
    "Microsoft could not complete sign-in because this app is not allowed to "
    "read calendars yet.\n\n"
    "Delegated Calendars.Read.Shared does not require admin consent by default, "
    "but some Microsoft 365 tenants block user consent. Ask an admin to grant "
    "Calendars.Read.Shared (and User.Read) for this app — no write permissions."
)


class OutlookAuthError(Exception):
    """Sign-in / token failure. consent_required is True when consent is blocked."""

    def __init__(self, message, consent_required=False):
        super().__init__(message)
        self.consent_required = consent_required


class OutlookGraphError(Exception):
    pass


def token_cache_path() -> str:
    return os.path.join(_get_app_dir(), TOKEN_CACHE_NAME)


def central_window_iso(start_d: date, end_d: date):
    """Inclusive date range as ISO-8601 datetimes with America/Chicago DST offset."""
    start_dt = datetime.combine(start_d, time.min, tzinfo=CENTRAL_TZ)
    end_dt = datetime.combine(end_d + timedelta(days=1), time.min, tzinfo=CENTRAL_TZ)
    return start_dt.isoformat(), end_dt.isoformat()


def _consent_required_from_error(exc) -> bool:
    text = str(exc or "").lower()
    markers = (
        "aadsts65001",
        "aadsts65004",
        "aadsts65005",
        "consent_required",
        "admin consent",
        "user declined to consent",
        "requires admin",
    )
    return any(m in text for m in markers)


def _load_msal():
    try:
        import msal
    except ImportError as e:
        raise OutlookAuthError(
            "The 'msal' package is not installed. Run: pip install msal"
        ) from e
    return msal


class OutlookGraphClient:
    """GET-only Graph helper. Construct with tenant_id + client_id from local config."""

    def __init__(self, tenant_id: str, client_id: str):
        self.tenant_id = (tenant_id or "").strip()
        self.client_id = (client_id or "").strip()
        if not self.tenant_id or not self.client_id:
            raise OutlookAuthError(
                "Enter the Microsoft Entra Application (client) ID and Directory "
                "(tenant) ID in Settings before signing in."
            )
        self._msal = _load_msal()
        self._cache = self._msal.SerializableTokenCache()
        self._load_cache()
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self._app = self._msal.PublicClientApplication(
            self.client_id,
            authority=authority,
            token_cache=self._cache,
        )

    def _load_cache(self):
        path = token_cache_path()
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._cache.deserialize(f.read())
            except Exception:
                logger.exception("Could not read MSAL token cache")

    def _save_cache(self):
        if not self._cache.has_state_changed:
            return
        path = token_cache_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._cache.serialize())
        except Exception:
            logger.exception("Could not write MSAL token cache")

    def _accounts(self):
        return self._app.get_accounts()

    def signed_in_account(self):
        accts = self._accounts()
        return accts[0] if accts else None

    def sign_out(self):
        for acct in list(self._accounts()):
            self._app.remove_account(acct)
        self._save_cache()
        path = token_cache_path()
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass

    def acquire_token(self, interactive=False) -> str:
        result = None
        accounts = self._accounts()
        if accounts:
            result = self._app.acquire_token_silent(READ_SCOPES, account=accounts[0])
        if not result and interactive:
            try:
                result = self._app.acquire_token_interactive(READ_SCOPES)
            except Exception as e:
                raise OutlookAuthError(str(e), consent_required=_consent_required_from_error(e)) from e
        if not result:
            raise OutlookAuthError(
                "Not signed in to Microsoft 365. Use Sign in from Settings."
            )
        self._save_cache()
        if "access_token" in result:
            return result["access_token"]
        err = result.get("error_description") or result.get("error") or "Token request failed."
        raise OutlookAuthError(err, consent_required=_consent_required_from_error(err))

    def _get_json(self, url, params=None, token=None):
        token = token or self.acquire_token(interactive=False)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Prefer": f'IdType="ImmutableId", outlook.timezone="{GRAPH_OUTLOOK_TZ}"',
        }
        resp = requests.get(url, headers=headers, params=params, timeout=60)
        if resp.status_code == 401:
            raise OutlookAuthError("Microsoft session expired. Sign in again.")
        if resp.status_code >= 400:
            raise OutlookGraphError(
                f"Graph read failed ({resp.status_code}): {resp.text[:500]}"
            )
        try:
            return resp.json()
        except json.JSONDecodeError as e:
            raise OutlookGraphError("Graph returned non-JSON data.") from e

    def _get_all_pages(self, url, params=None, token=None):
        """Follow @odata.nextLink until exhausted. Fail the whole fetch if any page fails."""
        token = token or self.acquire_token(interactive=False)
        items = []
        first = True
        while url:
            data = self._get_json(url, params=params if first else None, token=token)
            first = False
            params = None
            batch = data.get("value")
            items.extend(batch or [])
            url = data.get("@odata.nextLink")
        return items

    def get_me(self):
        return self._get_json(f"{GRAPH_ROOT}/me")

    def list_calendars(self):
        url = f"{GRAPH_ROOT}/me/calendars"
        params = {
            "$select": "id,name,owner,isDefaultCalendar,canEdit,isShared",
            "$top": "50",
        }
        return self._get_all_pages(url, params=params)

    def list_calendar_view(self, calendar_id: str, start_d: date, end_d: date):
        """All events in [start_d, end_d] inclusive (Central Time). Paginates fully."""
        start_iso, end_iso = central_window_iso(start_d, end_d)
        cal = quote(calendar_id, safe="")
        url = f"{GRAPH_ROOT}/me/calendars/{cal}/calendarView"
        params = {
            "startDateTime": start_iso,
            "endDateTime": end_iso,
            "$select": (
                "id,subject,start,end,isAllDay,categories,location,bodyPreview,"
                "lastModifiedDateTime,isCancelled"
            ),
            "$top": "100",
        }
        return self._get_all_pages(url, params=params)

    def test_calendar_read(self, calendar_id: str):
        today = date.today()
        events = self.list_calendar_view(calendar_id, today, today + timedelta(days=7))
        me = self.get_me()
        return {
            "user": me.get("displayName") or me.get("userPrincipalName") or "",
            "event_count": len(events),
        }
