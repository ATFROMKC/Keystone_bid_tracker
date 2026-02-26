# Moraware Integration Truth Order

Use this source order whenever Moraware behavior is unclear or conflicting.

## 1) Decompiled SDK (authoritative)

- `Moraware.JobTrackerAPI5.cs`
- Purpose: canonical API contract (XML envelope, command names, response schema, enum values).
- Key examples:
  - Root envelope: `MorawareCommand`
  - Session flow: `sessionCreate` -> `sessionId`
  - Job status source: `<job jobStatus="active|complete">`

## 2) Keystone URL/ID schema notes (instance-specific)

- `CHIP MOREAWARE MD FILES/Moraware_URL_Schema.md`
- Purpose: Keystone-specific IDs, `/sys/jobs` filter syntax, field codes.
- Use for:
  - Activity type IDs, status IDs, form IDs
  - Filter strings like `j19` job status filters
  - Column code mappings (for scraping/report queries)

## 3) App implementation (current runtime behavior)

- `keystone_bid_tracker/utils/moraware_client.py`
- Purpose: what this project actually does today.
- Check this before assuming behavior from older notes.

## 4) Context docs (supporting references)

- `CHIP MOREAWARE MD FILES/KEYSTONE_MORAWARE_SYSTEM_DOCUMENTATION.md`
- `CHIP MOREAWARE MD FILES/SECRET MORAWARE DISCOVERY-SUMMARY.md`
- Purpose: architecture and exploration context; useful but not canonical for protocol details.

## Escalation rule

If sources conflict:

1. Trust SDK (`Moraware.JobTrackerAPI5.cs`) first.
2. Adapt with Keystone schema notes (`Moraware_URL_Schema.md`) second.
3. Validate against current app code (`moraware_client.py`) third.
4. Use context docs only as background.

## Quick Rules for Future Debugging

- If XML payload shape is uncertain, check `Moraware.JobTrackerAPI5.cs` first (never guess root/command names).
- Prefer API for canonical status values; use `/sys/jobs` filters as fallback when needed.
- For job status filters in web URLs, use `j19` values from `Moraware_URL_Schema.md`:
  - `1 = Active`
  - `2 = Complete`
- When code/docs disagree, assume docs may be stale and validate against current `moraware_client.py` behavior.

## Confirmed APIErrorCodes_Enum (SDK)

- `1 = SessionTimedOut`
- `2 = InsufficientSecurityPrivileges`
- `3 = UnsupportedVersion`
- `4 = InvalidRequestDocument`
- `5 = UnsupportedCommand`
- `6 = LoginFailed`
- `7 = NonExistentObject`
