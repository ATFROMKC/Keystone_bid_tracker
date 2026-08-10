"""Background QThreads for Outlook read-only sync / test / calendar list."""

from datetime import date

from PyQt5.QtCore import QThread, pyqtSignal

from config import get_outlook_sync_config
from utils.outlook_graph_client import CONSENT_HINT, OutlookAuthError
from utils.outlook_board_sync import run_outlook_sync
from utils.outlook_provider import get_outlook_provider, normalize_provider_name


def _format_err(exc) -> str:
    msg = str(exc)
    if isinstance(exc, OutlookAuthError) and exc.consent_required:
        return CONSENT_HINT + "\n\nDetails: " + msg
    return msg


def _com_init_if_desktop(cfg):
    if normalize_provider_name(cfg.get("provider")) == "graph":
        return None
    try:
        import pythoncom
        pythoncom.CoInitialize()
        return pythoncom
    except ImportError:
        return None


def _com_uninit(pythoncom):
    if pythoncom is None:
        return
    try:
        pythoncom.CoUninitialize()
    except Exception:
        pass


class OutlookSignInWorker(QThread):
    """Graph-only interactive sign-in. Not used for Local Outlook Desktop."""

    finished = pyqtSignal(bool, str, object)

    def run(self):
        try:
            from utils.outlook_graph_client import OutlookGraphClient

            cfg = get_outlook_sync_config()
            client = OutlookGraphClient(cfg["tenant_id"], cfg["client_id"])
            client.acquire_token(interactive=True)
            me = client.get_me()
            name = me.get("displayName") or me.get("userPrincipalName") or "Signed in"
            self.finished.emit(True, f"Signed in as {name}.", me)
        except Exception as e:
            self.finished.emit(False, _format_err(e), None)


class OutlookListCalendarsWorker(QThread):
    finished = pyqtSignal(bool, str, object)

    def run(self):
        pc = None
        provider = None
        try:
            cfg = get_outlook_sync_config()
            pc = _com_init_if_desktop(cfg)
            provider = get_outlook_provider(cfg)
            cals = provider.list_calendars()
            self.finished.emit(True, f"Found {len(cals)} calendar(s).", cals)
        except Exception as e:
            self.finished.emit(False, _format_err(e), None)
        finally:
            provider = None
            _com_uninit(pc)


class OutlookTestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def run(self):
        pc = None
        provider = None
        try:
            cfg = get_outlook_sync_config()
            if not cfg.get("calendar_id"):
                self.finished.emit(False, "Select a calendar first.")
                return
            pc = _com_init_if_desktop(cfg)
            provider = get_outlook_provider(cfg)
            info = provider.test_calendar_read(cfg["calendar_id"])
            name = cfg.get("calendar_name") or "calendar"
            self.finished.emit(
                True,
                f"Read OK as {info.get('user') or 'signed-in user'}. "
                f"{name}: {info.get('event_count', 0)} event(s) in the next 7 days. "
                "Outlook was not modified.",
            )
        except Exception as e:
            self.finished.emit(False, _format_err(e))
        finally:
            provider = None
            _com_uninit(pc)


class OutlookSyncWorker(QThread):
    finished = pyqtSignal(bool, str, object)

    def __init__(self, db, start_d: date = None, end_d: date = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.start_d = start_d
        self.end_d = end_d

    def run(self):
        pc = None
        try:
            cfg = get_outlook_sync_config()
            pc = _com_init_if_desktop(cfg)
            result = run_outlook_sync(self.db, self.start_d, self.end_d)
            body = result.get("body_stats") or {}
            filled = int(body.get("filled") or 0)
            attempted = int(body.get("attempted") or result.get("fetched") or 0)
            hints = int(result.get("hint_candidate_count") or len(result.get("hint_candidates") or []))
            msg = (
                f"Synced {result['fetched']} Outlook event(s) "
                f"({result['start']} to {result['end']}): "
                f"{result['created']} new, {result['updated']} updated"
                + (f", {result['skipped']} skipped" if result.get("skipped") else "")
                + f". Bodies read: {filled}/{attempted}"
                + f" · Suggestions: {hints}"
                + ". Outlook was not modified."
            )
            if body.get("timed_out"):
                msg += (
                    " Appointment body fetch timed out (Outlook Trust Center may be "
                    "blocking); suggestions used Subject/Location only."
                )
            elif attempted and filled == 0 and (body.get("source") or "") == "desktop":
                msg += (
                    " No appointment bodies were readable; suggestions used "
                    "Subject/Location only."
                )
            self.finished.emit(True, msg, result)
        except Exception as e:
            self.finished.emit(False, _format_err(e), None)
        finally:
            _com_uninit(pc)
