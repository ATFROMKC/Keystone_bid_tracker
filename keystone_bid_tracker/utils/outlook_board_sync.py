"""
Outlook → Bid Board sync (one-way). Never writes to Outlook.

Fetch the full event set first; only then upsert SQLite rows.
Works with either Classic Outlook COM or Microsoft Graph via get_outlook_provider().
"""

from datetime import date, datetime, timedelta

from config import get_outlook_sync_config, save_outlook_sync_config
from utils.outlook_provider import get_outlook_provider, graph_event_to_neutral, normalize_provider_name
from utils.outlook_body_hints import combine_outlook_text, extract_hints

SOURCE_OUTLOOK = "OUTLOOK"
SOURCE_LOCAL = "LOCAL"

# Re-export for any callers that imported the Graph adapter from this module.
__all__ = [
    "SOURCE_OUTLOOK",
    "SOURCE_LOCAL",
    "map_outlook_categories",
    "resolve_outlook_status",
    "event_board_date",
    "event_location",
    "sync_date_window",
    "run_outlook_sync",
    "graph_event_to_neutral",
]


def _norm_cat(name) -> str:
    return " ".join(str(name or "").strip().lower().split())


def map_outlook_categories(categories, roster_names=None, category_map=None):
    """Return (estimator_or_None, board_status) from Outlook category names.

    Examples:
      Austin in Progress -> (Austin, IN_PROGRESS)
      Complete           -> (None or retained estimator, COMPLETE)
      Scott Complete     -> (Scott, COMPLETE)  # estimator + complete in one category
      Austin in Progress + Complete -> (Austin, COMPLETE)
    """
    cats = [_norm_cat(c) for c in (categories or []) if str(c or "").strip()]
    cmap = category_map or get_outlook_sync_config().get("category_map") or {}
    complete_names = {_norm_cat(n) for n in (cmap.get("complete_names") or [])}
    not_bid_names = {_norm_cat(n) for n in (cmap.get("not_bidding_names") or [])}
    est_map = {
        _norm_cat(k): (v or "").strip()
        for k, v in (cmap.get("estimator_in_progress") or {}).items()
        if k
    }

    is_complete = any(c in complete_names for c in cats)
    is_not_bidding = any(c in not_bid_names for c in cats)

    estimator = None
    roster = [n for n in (roster_names or []) if n]
    roster_l = {n.lower(): n for n in roster}

    for c in cats:
        if c in est_map and est_map[c]:
            estimator = est_map[c]
            break
        if c.endswith(" in progress"):
            stem = c[: -len(" in progress")].strip()
            if stem in roster_l:
                estimator = roster_l[stem]
                break
            if stem:
                estimator = stem.title() if not estimator else estimator
                break
        if c.endswith(" complete"):
            # "Scott Complete" / "Austin Complete" — estimator + COMPLETE in one tag
            stem = c[: -len(" complete")].strip()
            if stem and stem not in ("", "mark"):
                is_complete = True
                if stem in roster_l:
                    estimator = roster_l[stem]
                    break
                if not estimator:
                    estimator = stem.title()
                break

    if is_complete:
        return estimator, "COMPLETE"
    if is_not_bidding:
        return estimator, "NOT_BIDDING"
    return estimator, "IN_PROGRESS"


def resolve_outlook_status(local_row, outlook_status: str) -> str:
    """Outlook may promote to COMPLETE. Never undo a local Complete."""
    if outlook_status == "COMPLETE":
        return "COMPLETE"
    if not local_row:
        return outlook_status
    local_status = local_row.get("board_status") or "IN_PROGRESS"
    if local_status == "COMPLETE":
        return "COMPLETE"
    linked = int(local_row.get("linked_bid_count") or 0)
    if linked > 0 and outlook_status == "NOT_BIDDING":
        return local_status
    return outlook_status


def event_board_date(event) -> str:
    """Board date (YYYY-MM-DD) from a neutral provider event."""
    if event.get("is_all_day") or event.get("isAllDay"):
        start = event.get("start") or ""
        if isinstance(start, dict):
            return (start.get("date") or start.get("dateTime") or "")[:10]
        return str(start)[:10]
    start = event.get("start") or ""
    if isinstance(start, dict):
        if start.get("date"):
            return str(start.get("date"))[:10]
        return str(start.get("dateTime") or "")[:10]
    return str(start)[:10]


def event_location(event) -> str:
    loc = event.get("location") or ""
    if isinstance(loc, dict):
        return (loc.get("displayName") or "").strip()
    return str(loc or "").strip()


def week_start_on_or_before(day: date) -> date:
    """Monday of the week containing day (calendar tab is Monday-first)."""
    return day - timedelta(days=day.weekday())


def sync_date_window(start_d: date = None, end_d: date = None):
    cfg = get_outlook_sync_config()
    today = date.today()
    if start_d is None:
        if (cfg.get("sync_window") or "week_onward") == "week_onward":
            start_d = week_start_on_or_before(today)
        else:
            start_d = today - timedelta(days=cfg["lookback_days"])
    if end_d is None:
        end_d = today + timedelta(days=cfg["lookahead_days"])
    if end_d < start_d:
        start_d, end_d = end_d, start_d
    return start_d, end_d


def run_outlook_sync(db, start_d: date = None, end_d: date = None, client=None) -> dict:
    """Fetch all provider events, then upsert. Partial fetches never reach the DB."""
    cfg = get_outlook_sync_config()
    calendar_id = cfg.get("calendar_id") or ""
    if not calendar_id:
        raise ValueError("Select the shared Commercial Bid Calendar in Settings first.")
    if normalize_provider_name(cfg.get("provider")) == "graph":
        if not (cfg.get("tenant_id") and cfg.get("client_id")):
            raise ValueError(
                "Microsoft Graph requires tenant ID and client ID in Settings."
            )

    start_d, end_d = sync_date_window(start_d, end_d)
    provider = client if client is not None else get_outlook_provider(cfg)
    events = provider.list_events(calendar_id, start_d, end_d)
    body_stats = dict(getattr(provider, "body_stats", None) or {})
    if not body_stats:
        filled = sum(1 for e in events if (e.get("body") or "").strip())
        body_stats = {
            "filled": filled,
            "attempted": len(events),
            "timed_out": False,
            "source": "unknown",
        }

    try:
        roster = [r["name"] for r in db.get_estimators_roster(active_only=True) if r.get("name")]
    except Exception:
        roster = list(db.get_estimators() or [])

    try:
        customers = db.get_customers(active_only=True)
    except Exception:
        customers = []
    try:
        email_index = db.get_customer_email_index()
    except Exception:
        email_index = {}

    created = 0
    updated = 0
    skipped = 0
    changes = []
    hint_candidates = []
    cust_by_id = {int(c["id"]): c for c in customers if c.get("id") is not None}

    for ev in events:
        if ev.get("is_cancelled") or ev.get("isCancelled"):
            skipped += 1
            continue
        event_id = (ev.get("source_event_id") or ev.get("id") or "").strip()
        cal_id = (ev.get("source_calendar_id") or calendar_id or "").strip()
        if not event_id:
            skipped += 1
            continue
        board_date = event_board_date(ev)
        if len(board_date) != 10:
            skipped += 1
            continue
        estimator, ol_status = map_outlook_categories(
            ev.get("categories"), roster, cfg.get("category_map")
        )
        existing = db.get_board_item_by_outlook_event(cal_id, event_id)
        status = resolve_outlook_status(existing, ol_status)
        text = combine_outlook_text(
            ev.get("subject"), event_location(ev), ev.get("body") or ev.get("bodyPreview")
        )
        hints = extract_hints(
            text, board_date=board_date, customers=customers, email_to_customer_id=email_index
        )
        body = (ev.get("body") or ev.get("bodyPreview") or "").strip() or None
        if body is None and existing:
            source_notes = existing.get("outlook_source_notes")
        else:
            source_notes = body
        subject = ev.get("subject") or "(No subject)"
        _id, was_new = db.upsert_outlook_board_item(
            cal_id,
            event_id,
            subject,
            board_date,
            estimator=estimator,
            board_status=status,
            location=event_location(ev),
            source_notes=source_notes,
            last_modified=ev.get("last_modified") or ev.get("lastModifiedDateTime"),
        )
        item = db.get_board_item(_id) or {}
        due_suggest = hints.get("suggested_due_date")
        cust_ids = list(hints.get("suggested_customer_ids") or [])
        unmatched = list(hints.get("unmatched_emails") or [])
        needs_due = bool(due_suggest and not (item.get("actual_due_date") or "").strip())
        try:
            existing_custs = db.get_board_item_customers(_id) or []
        except Exception:
            existing_custs = []
        needs_accounts = bool(cust_ids) and len(existing_custs) == 0
        if needs_due or needs_accounts or unmatched:
            hint_candidates.append({
                "item_id": _id,
                "bid_name": subject,
                "board_date": board_date,
                "suggested_due_date": due_suggest if needs_due else None,
                "suggested_customer_ids": cust_ids if needs_accounts else [],
                "suggested_customer_names": [
                    (cust_by_id.get(int(cid)) or {}).get("name") or f"#{cid}"
                    for cid in (cust_ids if needs_accounts else [])
                ],
                "unmatched_emails": unmatched,
                "apply_due": needs_due,
                "apply_accounts": needs_accounts,
            })
        changes.append({
            "item_id": _id,
            "bid_name": subject,
            "board_date": board_date,
            "action": "new" if was_new else "updated",
        })
        if was_new:
            created += 1
        else:
            updated += 1

    now_iso = datetime.now().isoformat(timespec="seconds")
    save_outlook_sync_config({"last_synced_at": now_iso})
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "fetched": len(events),
        "due_hints": 0,
        "account_hints": 0,
        "hint_candidates": hint_candidates,
        "hint_candidate_count": len(hint_candidates),
        "body_stats": body_stats,
        "changes": changes[:50],
        "start": start_d.isoformat(),
        "end": end_d.isoformat(),
        "last_synced_at": now_iso,
    }
