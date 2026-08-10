"""
Suggest Actual Due Date and Accounts from Outlook appointment text.

Used by Outlook → Bid Board sync. Suggestions are applied only when the board
item fields are empty — never overwrite local Actual Due Date or Accounts.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from email.utils import parseaddr

# Explicit due-date cues (avoid bare dates that look like phone numbers / SF).
_DUE_PATTERNS = [
    re.compile(
        r"(?i)\b(?:bid\s+)?due(?:\s+date)?\b(?:\s*(?:is|:|-))?\s*"
        r"(?P<date>"
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?"
        r"|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{2,4})?"
        r")"
    ),
    re.compile(
        r"(?i)\bbid\s+date\s+(?:moved\s+to|is|to|:)?\s*"
        r"(?P<date>\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)"
    ),
]

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I)

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def strip_html(text: str) -> str:
    raw = str(text or "")
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = raw.replace("\xa0", " ").replace("\r", "\n")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def combine_outlook_text(subject=None, location=None, body=None) -> str:
    parts = []
    for p in (subject, location, body):
        t = strip_html(p or "")
        if t:
            parts.append(t)
    return "\n".join(parts)


def _parse_date_token(token: str, ref: date) -> date | None:
    token = (token or "").strip().rstrip(".,;")
    if not token:
        return None
    token = re.sub(r"(?i)(\d+)(st|nd|rd|th)\b", r"\1", token)

    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y", "%m/%d", "%m-%d"):
        try:
            dt = datetime.strptime(token, fmt)
            year = dt.year
            if fmt in ("%m/%d", "%m-%d"):
                year = ref.year
                cand = date(year, dt.month, dt.day)
                # If the bare month/day is far behind the board date, prefer next year
                if cand < ref - timedelta(days=180):
                    try:
                        cand = date(year + 1, dt.month, dt.day)
                    except ValueError:
                        pass
                return cand
            if year < 100:
                year += 2000
            return date(year, dt.month, dt.day)
        except ValueError:
            pass

    m = re.match(
        r"(?i)^(?P<mon>[a-z]+)\s+(?P<day>\d{1,2})(?:,?\s*(?P<year>\d{2,4}))?$",
        token,
    )
    if m:
        mon = _MONTHS.get(m.group("mon").lower())
        if not mon:
            return None
        day = int(m.group("day"))
        year_raw = m.group("year")
        if year_raw:
            year = int(year_raw)
            if year < 100:
                year += 2000
        else:
            year = ref.year
        try:
            cand = date(year, mon, day)
        except ValueError:
            return None
        if not year_raw and cand < ref - timedelta(days=180):
            try:
                cand = date(year + 1, mon, day)
            except ValueError:
                pass
        return cand
    return None


def suggest_due_date(text: str, board_date: str = None) -> str | None:
    """Return YYYY-MM-DD if a due-date cue is found, else None."""
    blob = strip_html(text)
    if not blob:
        return None
    ref = date.today()
    if board_date and len(str(board_date)[:10]) == 10:
        try:
            ref = date.fromisoformat(str(board_date)[:10])
        except ValueError:
            pass
    for pat in _DUE_PATTERNS:
        m = pat.search(blob)
        if not m:
            continue
        parsed = _parse_date_token(m.group("date"), ref)
        if parsed:
            return parsed.isoformat()
    return None


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def suggest_customer_ids(text: str, customers: list, email_to_customer_id: dict = None) -> list:
    """Return unique customer ids confidently mentioned in text.

    Prefers email hits, then whole-name matches (longer names first).
    """
    blob = strip_html(text)
    if not blob:
        return []
    blob_l = blob.lower()
    found = []
    seen = set()

    email_map = email_to_customer_id or {}
    for m in _EMAIL_RE.finditer(blob):
        email = m.group(0).lower()
        _, addr = parseaddr(email)
        addr = (addr or email).lower().strip()
        cid = email_map.get(addr)
        if cid and cid not in seen:
            seen.add(cid)
            found.append(cid)

    # Longest names first so "Higgins Construction" wins over "Higgins"
    ranked = sorted(
        [c for c in (customers or []) if (c.get("name") or "").strip()],
        key=lambda c: len(c["name"].strip()),
        reverse=True,
    )
    for c in ranked:
        name = c["name"].strip()
        cid = c.get("id")
        if not cid or cid in seen:
            continue
        n = _norm_name(name)
        if len(n) < 3:
            continue
        # Whole-phrase match with non-alnum boundaries
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", re.I)
        if pat.search(blob_l):
            seen.add(cid)
            found.append(cid)

    # Drop shorter names that are contained in a longer matched name
    # ("Higgins" inside "Higgins Construction").
    name_by_id = {
        c["id"]: _norm_name(c.get("name") or "")
        for c in (customers or [])
        if c.get("id") is not None
    }
    pruned = []
    for cid in found:
        n = name_by_id.get(cid) or ""
        if any(
            n and n != (name_by_id.get(other) or "") and n in (name_by_id.get(other) or "")
            for other in found
        ):
            continue
        pruned.append(cid)
    return pruned


def list_unmatched_emails(text: str, email_to_customer_id: dict = None) -> list:
    """Emails found in text that are not linked to an existing account contact."""
    blob = strip_html(text)
    if not blob:
        return []
    email_map = email_to_customer_id or {}
    found = []
    seen = set()
    for m in _EMAIL_RE.finditer(blob):
        email = m.group(0).lower()
        _, addr = parseaddr(email)
        addr = (addr or email).lower().strip()
        if not addr or addr in seen:
            continue
        seen.add(addr)
        if addr not in email_map:
            found.append(addr)
    return found


def extract_hints(text: str, board_date: str = None, customers: list = None,
                  email_to_customer_id: dict = None) -> dict:
    return {
        "suggested_due_date": suggest_due_date(text, board_date),
        "suggested_customer_ids": suggest_customer_ids(
            text, customers or [], email_to_customer_id or {}
        ),
        "unmatched_emails": list_unmatched_emails(text, email_to_customer_id or {}),
    }
