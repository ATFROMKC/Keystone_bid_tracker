# Config and secrets (BidTracker)

## Bottom line

BidTracker stores machine-local settings in **`keystone_bid_tracker/config.json`**, which is **gitignored**. Graph auth tokens live in **`msal_token_cache.bin`** (also gitignored). **Never** commit credentials, prod keys, or personal Moraware/Outlook secrets into tracked files.

**CounterPro:** same rule — no credentials in repo; Austin/agents must **not** receive production keys. Use CounterPro’s existing secret stores / env / Azure patterns, not BidTracker’s local JSON as a template to check in.

## Config file location

| Item | Detail |
|---|---|
| Path | `keystone_bid_tracker/config.json` (next to the package / frozen exe via `_get_app_dir()`) |
| API | `config.get_config()` / `save_config()` in `keystone_bid_tracker/config.py` |
| Git | Listed in `.gitignore` as `keystone_bid_tracker/config.json` |
| Auto field | `last_opened` (ISO date) written on every `save_config` |

Missing file → empty dict (defaults apply in getters).

## Common top-level keys

| Key | Purpose |
|---|---|
| `database_path` | SQLite DB path |
| `dropbox_bids_path` | Root folder for year/bid file layout |
| `bid_board_files_path` | Optional override for Bid Board attachment copies (else `<db_dir>/BidBoardFiles`) |
| `moraware_url` | Moraware base URL (scheme + host; path normalized in client) |
| `moraware_username` | Moraware login (local secret) |
| `moraware_password` | Moraware password (local secret) |
| `estimator_colors` | `{ estimator_name: "#hex" }` overrides for Bid Board cards |
| `complete_blue` | Color for COMPLETE board cards |
| `current_estimator` | This machine’s “Assign to Me” identity (opt-in string; no login system) |
| `calendar_view` | `month` \| `3week` \| `week` \| `day` |
| `hide_weekends` | bool |
| `last_portal` | `hub` \| `estimator` \| `pm` |
| `outlook_sync` | Nested object (see below) |
| `last_opened` | Last config save date |

Exact key set evolves with Settings UI; treat `config.py` getters as the authoritative list for defaults and validation.

## Nested `outlook_sync`

Defaults and merge logic: `get_outlook_sync_config()` / `save_outlook_sync_config()`.

| Key | Default / notes |
|---|---|
| `provider` | `desktop` or `graph` (default `desktop`) |
| `sync_window` | `week_onward` (default) or `rolling` |
| `lookback_days` | `60` (rolling start) |
| `lookahead_days` | `120` |
| `read_appointment_bodies` | bool (default True) |
| `client_id` | Azure app (Graph) |
| `tenant_id` | Azure tenant (Graph) |
| `calendar_id` | Selected shared calendar id (`com:…` or Graph id) |
| `calendar_name` / `calendar_owner` / `calendar_store_id` / `calendar_path` | Display / COM metadata |
| `last_synced_at` | ISO timestamp from last successful sync |
| `category_map` | `complete_names`, `not_bidding_names`, `estimator_in_progress` |

Graph client id / tenant id are **not** passwords, but they are environment-specific — keep them out of git unless the project explicitly documents a public-client id as non-secret (still prefer local config).

## MSAL token cache

| Item | Detail |
|---|---|
| File | `msal_token_cache.bin` (app dir; also `**/msal_token_cache.bin` in `.gitignore`) |
| Used by | Graph Outlook client (`outlook_graph_client.py`) |
| Content | Delegated user tokens — **secret**; never commit or zip into handoff packages without scrubbing |

## What must never be tracked

- Moraware username/password
- MSAL / OAuth refresh tokens and `msal_token_cache.bin`
- Production Azure client secrets (BidTracker Graph path is public-client oriented; CounterPro must not invent secrets into git)
- Live `config.json` from any Keystone machine
- Prod API keys, Supabase service roles, Render env dumps for Austin or agents

## CounterPro guidance

1. **Never** put credentials in tracked files (`backend/`, `frontend/`, docs, handoff zips).
2. **Do not** distribute Keystone prod Moraware or M365 credentials to Austin or coding agents.
3. Prefer CounterPro’s established secret management (host env, Azure Key Vault, etc.).
4. BidTracker `config.json` shape is **reference for which settings exist**, not a file to copy into the CounterPro repo.
5. When packaging handoff zips, exclude `config.json`, token caches, and diagnostic HTML that may contain session-specific data.

## Related docs

- [moraware.md](moraware.md) — Moraware credentials usage (read-only BidTracker; CounterPro REUSE)
- [outlook-readonly-sync.md](outlook-readonly-sync.md) — Graph vs COM and sync settings
- Repo `.gitignore` — canonical ignore list for secrets and caches
