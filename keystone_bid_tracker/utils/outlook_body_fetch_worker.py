"""
Worker: read Classic Outlook appointment bodies by EntryID (read-only).

Invoked as a subprocess so a hung Body access can be killed without freezing
the Bid Tracker UI thread. Prints one JSON object per line.
"""

from __future__ import annotations

import json
import sys


def fetch_bodies(entry_ids, max_chars: int = 1200):
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    results = []
    try:
        app = win32com.client.GetActiveObject("Outlook.Application")
        ns = app.GetNamespace("MAPI")
        for eid in entry_ids:
            rec = {"id": eid, "body": "", "ok": False}
            try:
                item = ns.GetItemFromID(eid)
                text = ""
                try:
                    text = str(item.Body or "")
                except Exception:
                    try:
                        text = str(
                            item.PropertyAccessor.GetProperty(
                                "http://schemas.microsoft.com/mapi/proptag/0x1000001F"
                            )
                            or ""
                        )
                    except Exception:
                        text = ""
                rec["body"] = text[:max_chars]
                rec["ok"] = True
            except Exception as e:
                rec["error"] = str(e)
            results.append(rec)
            print(json.dumps(rec), flush=True)
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass
    return results


def main():
    raw = sys.stdin.read() or "[]"
    try:
        entry_ids = json.loads(raw)
    except json.JSONDecodeError:
        entry_ids = []
    if not isinstance(entry_ids, list):
        entry_ids = []
    fetch_bodies([str(x) for x in entry_ids if x])


if __name__ == "__main__":
    main()
