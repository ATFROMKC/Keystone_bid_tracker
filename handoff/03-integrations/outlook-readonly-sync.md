# Outlook → Bid Board (read-only sync)

## Bottom line

Outlook sync is **one-way into BidTracker** (create/update board items). It **never writes back** to Outlook.

**CRITICAL — COM is temporary.** Classic Outlook **desktop COM** is a **workaround** while waiting on Azure AD **admin consent** for Microsoft Graph `Calendars.Read.Shared`. **Graph is already implemented** and is the **intended long-term** path. For **CounterPro (hosted):** COM is **not viable** on the server — plan **server-side Graph** (or existing M365 integration). Treat COM as functional desktop reference only.

## Framing

| Role | Meaning |
|---|---|
| BidTracker HOW | Dual providers (COM today default; Graph ready); upsert into SQLite Bid Board |
| CounterPro WHAT | Same business rules (status promote/demote, hints, categories) over Graph on the host |

## Hard read-only rules

| Surface | Forbidden |
|---|---|
| **Microsoft Graph** | No calendar **POST / PATCH / DELETE** (or any write) to events/calendars |
| **Classic COM** | Never call **Save / Delete / Move / Send**; no property mutations that persist |

Sync only **lists/reads** events, then upserts **local** `bid_board_items`.

## Providers

Configured via `outlook_sync.provider` (`desktop` | `graph`). Factory: `utils/outlook_provider.py` → `get_outlook_provider()`.

| Provider | Identity of events | Notes |
|---|---|---|
| **desktop** (COM) | Calendar / event ids use Classic Outlook **EntryID**; calendar ids often prefixed `com:{EntryID}` | Requires Windows + Classic Outlook; shared calendar walk |
| **graph** | Graph calendar id + event id | MSAL public client; needs `tenant_id`, `client_id`, admin consent for `Calendars.Read.Shared` (+ `User.Read`) |

Neutral event shape (subject, start/end, categories, location, body, cancelled flag, source ids) is shared so `run_outlook_sync` is provider-agnostic.

## Upsert key

Unique local identity for Outlook-sourced rows:

`(outlook_calendar_id, outlook_event_id)`

Index: `idx_board_outlook_event` (partial unique where `outlook_event_id IS NOT NULL`). Lookup: `Database.get_board_item_by_outlook_event` → `upsert_outlook_board_item`.

## Sync window (Windows BidTracker defaults)

| Mode | `sync_window` | Range |
|---|---|---|
| **This week onward** (default) | `week_onward` | Monday of current week → today + **lookahead** (default **120** days) |
| **Rolling** | `rolling` | today − **lookback** (default **60**) → today + **lookahead** (**120**) |

Helpers: `sync_date_window()`, Settings combo in `ui/settings_tab.py`.

## Fetch-then-upsert

`run_outlook_sync` in `outlook_board_sync.py`:

1. Resolve date window and provider.
2. **Fetch the full event set** for the window.
3. Only then upsert SQLite rows (partial fetches must not half-update the board).
4. Persist `outlook_sync.last_synced_at`.

Cancelled / missing id / bad board date → skipped.

## Status rules (categories → board)

Categories map via `category_map` (complete names, not-bidding names, optional estimator overrides) plus patterns like `"Austin in Progress"` / `"Scott Complete"`.

`resolve_outlook_status(local_row, outlook_status)`:

| Rule | Behavior |
|---|---|
| Outlook says **COMPLETE** | May **promote** local status to COMPLETE |
| Local already **COMPLETE** | **Never demote** (Outlook cannot undo Complete) |
| Item has **linked bids** and Outlook says **NOT_BIDDING** | **Block** NOT_BIDDING override — keep local status |
| Otherwise | Accept Outlook-derived status (`IN_PROGRESS` / `NOT_BIDDING` / `COMPLETE`) |

## Hints (due date / accounts)

After upsert, text from subject + location + body is scanned (`outlook_body_hints.extract_hints`):

- Suggest **Actual Due Date** and **Accounts** (matched customers / emails).
- Candidates go to **`OutlookHintReviewDialog`** — user checks rows to apply.
- Apply **only when fields are empty** (never overwrite existing due date or accounts).
- **Never auto-create accounts**; unmatched emails are shown for awareness only.

Optional COM body enrichment: `outlook_body_fetch_worker.py` (read-only EntryID body fetch).

## CounterPro direction

- Implement **server-side Graph** read of the shared Commercial Bid Calendar.
- Preserve promote/demote and linked-bid NOT_BIDDING guards.
- Keep hint apply as explicit user confirmation; empty-field-only; no auto-create customers.
- Do not depend on Classic Outlook COM in Render/Linux hosting.

## Key files (reference)

| Path | Role |
|---|---|
| `utils/outlook_board_sync.py` | Window, category map, status resolve, fetch-then-upsert |
| `utils/outlook_provider.py` | Provider factory + Graph→neutral mapping |
| `utils/outlook_com_client.py` | Classic COM read-only client (`com:` ids) |
| `utils/outlook_graph_client.py` | Graph read-only client (MSAL) |
| `utils/outlook_body_hints.py` | Due/account extraction |
| `utils/outlook_body_fetch_worker.py` | Async COM body fill |
| `utils/outlook_sync_worker.py` | Qt worker wrapping sync |
| `ui/outlook_hint_review_dialog.py` | Review/apply suggestions |
| `ui/calendar_tab.py` | Sync button / last-synced label |
| `ui/settings_tab.py` | Provider, window, Graph ids, calendar pick |
| `config.py` | `get_outlook_sync_config` / defaults |
| `database.py` | `upsert_outlook_board_item`, unique Outlook index |

Token cache for Graph: gitignored `msal_token_cache.bin` — see [config-and-secrets.md](config-and-secrets.md).
