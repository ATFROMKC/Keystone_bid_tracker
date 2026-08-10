# Moraware integration (BidTracker reference)

## Bottom line

BidTracker’s Moraware client is **read-oriented reference only**. CounterPro **already owns Moraware** via `backend/` + `tools/moraware-cli` + `azure-moraware-function`. **Do not port** `moraware_client.py`. Porting would duplicate CounterPro’s stack and risk Moraware’s **one-session-per-user** rule (kicking live users / automation conflicts).

**CounterPro direction:** REUSE existing Moraware backend paths. Never log in as the automation user or as “chip” from BidTracker-style desktop credentials.

## Framing

| Role | Meaning |
|---|---|
| BidTracker HOW | Optional comparison — hybrid web session + scrape + XML API v5 in Python |
| CounterPro WHAT | Canonical Moraware ownership; BidTracker proves *which* job/phase fields matter for commercial bids |

## Truth order (when sources conflict)

1. **Decompiled SDK** — `reference/Moraware.JobTrackerAPI5.cs` (envelope, commands, enums, response shape)
2. **Tenant URL/ID schema** — `reference/chip-moraware-md-files/Moraware_URL_Schema.md` (Keystone field IDs, `/sys/jobs` filters, activity/form codes)
3. **BidTracker runtime** — `keystone_bid_tracker/utils/moraware_client.py` (what this app actually does today)
4. **Notes / cheatsheets** — `keystone_bid_tracker/docs/moraware/*`, other chip-moraware notes (background only)

Escalation: SDK → schema → code → notes. Prefer API for canonical status; use web filters as fallback when needed.

## Hybrid architecture (BidTracker)

BidTracker uses **three complementary channels**, not API-only:

| Channel | Purpose |
|---|---|
| **Web session login** | Cookie session for HTML pages and AJAX |
| **Scrape** | `/sys/jobs` list, job detail pages, Job Ticket A form content via AJAX expand |
| **XML API v5** | `POST` to `/api.aspx` (`sessionCreate`, `jobQuery`, `jobActivityQuery`, …) |

Login establishes the browser-like session; API uses a separate `sessionId` from `sessionCreate`. Fast sync prefers API queries; scrapes fill gaps.

## Fast sync (`use_fast_sync`, default `True`)

- Constructor flag: `MorewareClient(..., use_fast_sync=True)` (default **True**).
- Fast path: **`jobActivityQuery` / `jobQuery`** for jobs, activities, custom fields, status.
- **Scrape fallbacks** when API rows miss TP / sq ft / job number / phases (Job Ticket A AJAX, invoice activity tables, job detail).
- **Calendar activity-id stub:** `_fetch_calendar_activity_ids(...)` currently returns an **empty list**. Date/type-only calendar discovery is not available in this tenant’s API schema; fast flow uses **batched-per-job** API queries instead. Treat the stub as intentional, not unfinished “call the calendar.”

## Data BidTracker cares about

Per linked Moraware job / phase (fed into local `invoice_data` and PM views):

| Field | Notes |
|---|---|
| **phase** | Job Ticket A / activity phase labels |
| **tp_code** | Currency-like “TP” custom field |
| **sq_ft** | Square footage custom field |
| **dates** | Invoice / template / schedule dates as available |
| **invoice_status** | Typically Pending vs Complete (normalized from activity status text) |

**Combined phases:** Labels like `ST1, ST2` (also `/`, `&`, `+`, `and`) are **split and reconciled** onto Job Ticket A phase names via `_split_phase_tokens` / `_resolve_activity_phase_targets` so one activity can map to multiple ticket phases.

## Tenant-specific IDs (Keystone)

Hard-coded / schema-documented for this Moraware instance:

| ID | Meaning |
|---:|---|
| **71** | Activity custom field — TP |
| **72** | Activity custom field — SQ FT |
| **13** | Job custom field — job number |
| **29** | `MORAWARE_CUID` — customer/instance id used in Job Ticket A AJAX (`cuid=29`) |

Do not assume these IDs on other tenants without schema confirmation.

## Job number vs job id

| Concept | What it is | Use |
|---|---|---|
| **Moraware job id** | Internal numeric id in URLs / API `job id=` | Linking, Open URL, primary key for sync |
| **Job number** | Human-facing custom field (id **13**) | Display, matching, Dropbox folder naming helpers |

**Open in Moraware URL:** `{origin}/sys/job/{moraware_job_id}`  
(`origin` = scheme + host from configured `moraware_url`; path uses **job id**, not job number.)

## Read-oriented stance

BidTracker logs in to **read** lists, details, ticket forms, and API queries for sync overlays. It is not CounterPro’s write/automation surface. Any CounterPro write paths stay in CounterPro’s Moraware tooling.

## CounterPro anti-duplication (critical)

1. **REUSE** `backend/` Moraware services, caches, and sync windows.
2. **REUSE** `tools/moraware-cli/` (C# / SOAP SDK) and `azure-moraware-function/` (.NET Framework host for the SDK).
3. **Do not** copy BidTracker’s credentialed Python login into Render or into agent workflows.
4. **Never** authenticate as the shared automation user or as chip’s personal Moraware session for exploratory scraping from BidTracker patterns — session eviction is real.
5. Map BidTracker’s phase/TP/sq-ft needs onto **existing** Moraware-cache tables; do not invent a parallel invoice cache.

## Key files (reference)

| Path | Role |
|---|---|
| `keystone_bid_tracker/utils/moraware_client.py` | Hybrid client (web + scrape + API v5) |
| `keystone_bid_tracker/docs/moraware/*` | Truth-order note, field dumps, scraping cheatsheet |
| `keystone_bid_tracker/docs/BID_TRACKER_MORAWARE_FAST_SYNC_MIGRATION.md` | Fast-sync design history |
| `reference/Moraware.JobTrackerAPI5.cs` | SDK contract |
| `reference/chip-moraware-md-files/*` | Tenant schema + discovery notes |
| `ui/moraware_sync_dialog.py`, `ui/pm_active_jobs_tab.py`, sync workers | Consumers of the client |

Config credentials for BidTracker live in gitignored `config.json` (`moraware_url`, `moraware_username`, `moraware_password`) — see [config-and-secrets.md](config-and-secrets.md).
