# Keystone Bid Tracker → CounterPro Handoff Package

**START HERE.**

This folder is documentation only. It describes what the current **Keystone Bid Tracker** desktop app does today (business rules, data relationships, invariants) so Chip’s agent can integrate commercial estimating / bid-management workflows into the **Keystone Pricing Portal** (CounterPro) — **reusing what CounterPro already has**, and building only what is genuinely missing, **in CounterPro’s own style**.

## What this is / what this is not

| This package IS | This package is NOT |
|---|---|
| An accurate audit of BidTracker behavior (code is source of truth) | A port or rewrite of BidTracker into React/TS |
| Requirements + proven business logic worth preserving | A spec that CounterPro must copy line-for-line |
| A Reuse / Extend / Map / Add mapping process | Permission to override CounterPro systems |
| Destination constraints from Chip’s CounterPro onboarding docs | An assumption about CounterPro table names you haven’t inspected |

**BidTracker code** (`keystone_bid_tracker/`) remains the working prototype and source of truth for BidTracker behavior.  
**CounterPro’s own `CLAUDE.md` / docs / guardrails** remain the source of truth for CounterPro constraints. Where this handoff and CounterPro’s docs disagree on CounterPro matters, **CounterPro wins**.

## Framing for Chip’s agent

1. **Requirements first** — WHAT / WHY (rules, relationships, invariants) is authoritative.
2. **Implementation as reference** — HOW BidTracker did it (PyQt, SQLite, file paths) is optional comparison material, not a template to copy.
3. **Anti-duplication is the primary guardrail** — do not rebuild anything CounterPro already provides.
4. **Implement in CounterPro’s idiom** — Express + TypeScript in `backend/`, migrations in `database/migrations/`, React 18 surfaces in existing portals.

## Required approach (do this in order)

1. Read CounterPro’s own guardrails first (`/CLAUDE.md`, nearest-folder `CLAUDE.md`, `docs/moraware/INDEX.md`, `docs/AGENT-PLAYBOOK.md`, `docs/PORTAL-FEATURES.md`).
2. Inspect existing CounterPro functionality (especially the retired commercial estimator, `staffService.ts`, Moraware caches) before proposing changes.
3. Map each BidTracker concept as **REUSE / EXTEND / MAP / ADD** (reuse-first bias).
4. Get Chip’s review before conflicting or destructive changes.
5. Never bypass CounterPro’s canonical users, permissions, routing, Moraware, staff-split, pricing/COGS systems.

Copy-paste kickoff: [`04-migration-to-counterpro/agent-kickoff-prompt.md`](04-migration-to-counterpro/agent-kickoff-prompt.md)

## Reading order

| Order | Doc | Purpose |
|------:|-----|---------|
| 1 | [`00-orientation/project-overview.md`](00-orientation/project-overview.md) | What BidTracker is, maturity, portals |
| 2 | [`00-orientation/glossary.md`](00-orientation/glossary.md) | Bid vs board item vs revision vs job vs link… |
| 3 | [`00-orientation/architecture.md`](00-orientation/architecture.md) | Runtime / portals / data flow |
| 4 | [`01-data-model/`](01-data-model/) | Schema, ERD, invariants |
| 5 | [`02-workflows/`](02-workflows/) | Estimator + Bid Board + PM workflows |
| 6 | [`03-integrations/`](03-integrations/) | Moraware (reference only) + Outlook (COM workaround / Graph intended) |
| 7 | [`04-migration-to-counterpro/`](04-migration-to-counterpro/) | Destination constraints + mapping process |
| 8 | [`05-known-gaps.md`](05-known-gaps.md) | Unfinished / unwired / temporary workarounds |

Also open the **live BidTracker source** beside these docs — especially `keystone_bid_tracker/database.py`.

## Confirmed CounterPro stack (destination facts)

From Chip’s onboarding docs (not invented here):

| Piece | What it is |
|---|---|
| `frontend/` | React 18 + TypeScript + Vite (Admin, B2B, kiosk, TV, field portals) |
| `backend/` | Node + Express + TypeScript on Render — all business logic and every Moraware integration |
| `database/` | Supabase (Postgres); migrations in `database/migrations/` |
| `tools/moraware-cli/` | C# CLI speaking Moraware SOAP SDK |
| `azure-moraware-function/` | Azure Function (Moraware SDK is .NET Framework; Render is Linux) |

**Moraware is the ERP point of truth.** Almost every Supabase table is a cache of Moraware with a sync window. Treat Supabase as stale until proven fresh.

## Highest-value anti-duplication checks (read before building)

1. **Do not port BidTracker’s Moraware client.** CounterPro already owns Moraware via `backend/` + `moraware-cli` + Azure Function. Porting BidTracker’s credentialed login would also violate Moraware’s one-session-per-user rule.
2. **Audit the retired commercial estimator first** (`commercialEstimatingService.ts` / `routes/commercialEstimating.ts`) and confirm direction with Chip before adding BidTracker-like surfaces.
3. **Map `invoice_data` / phases** onto existing Moraware-cache tables — do not create a parallel invoice cache.
4. Genuine **ADD** candidates are mostly non-Moraware: bids, revisions, bid-board opportunities, board↔bid links, allocations, parent/child split bids, Outlook-sourced board items (Graph path).

## Outlook note (design intent)

BidTracker’s Classic Outlook **COM/desktop** sync is a **temporary workaround** while Azure AD admin consent for Microsoft Graph (`Calendars.Read.Shared`) is pending. Graph is already implemented in BidTracker and is the intended long-term path. For CounterPro (hosted web), desktop COM is not viable — plan a server-side Graph (or existing M365) integration; treat COM as functional reference only.

## Package contents

```
handoff/
  README.md
  00-orientation/
  01-data-model/          # schema-reference, erd, schema.sql, invariants
  02-workflows/
  03-integrations/
  04-migration-to-counterpro/
  05-known-gaps.md
```

## Helper scripts

| Script | Purpose |
|---|---|
| `scripts/make_handoff_zip.ps1` | Clean zip of the repo for sharing (excludes `config.json`, `.venv`, `__pycache__`, build junk, packages zips) |
| `scripts/export_handoff_schema.py` | Regenerates `handoff/01-data-model/schema.sql` from `Database.init_db()` |

No BidTracker application code was changed for this package (docs + helpers + light `.gitignore` hygiene only).
