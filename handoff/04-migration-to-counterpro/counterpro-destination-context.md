# CounterPro destination context

**Bottom line:** This file captures Chip’s CounterPro constraints for the *receiving* agent. It is destination context only — it must not change BidTracker code or behavior. Where this handoff and CounterPro’s own docs disagree on CounterPro matters, **CounterPro wins** (`CLAUDE.md`, `READ-ME-FIRST` / `GROUND-RULES`, nearest-folder docs).

Source summary: Chip’s `READ-ME-FIRST.md` and `GROUND-RULES.md` (tracked as repo `CLAUDE.md` / local `CLAUDE.local.md` after setup). Re-read those in the CounterPro repo; do not treat this handoff as a substitute.

---

## Confirmed stack

| Piece | What it is |
|---|---|
| `frontend/` | React 18 + TypeScript + Vite (Admin, B2B, kiosk, TV, field portals) |
| `backend/` | Node + Express + TypeScript on Render — all business logic and every Moraware integration |
| `database/` | Supabase (Postgres); migrations in `database/migrations/` |
| `tools/moraware-cli/` | C# CLI speaking the Moraware SOAP SDK |
| `azure-moraware-function/` | Azure Function (Moraware SDK is .NET Framework; Render is Linux) |

**Moraware is the ERP point of truth** for jobs, activities, phases, slabs, and invoicing. Almost every Supabase table is a *cache* of Moraware with a sync window and baked-in assumptions. **Treat Supabase as stale until proven fresh.**

---

## Hard rules (incident-backed)

1. **Never push to `main`.** Pushing `main` *is* deploying to production. Render auto-deploys (~2 min), no staging, no undo. Workflow: branch → commit → push to **fork** → PR → Chip merges.
2. **No production credentials.** Do not request Supabase service key, Render API key, Azure function key, or Moraware backend password. Never write credentials into tracked files, fixtures, samples, or comments (tripwire fires).
3. **Moraware = ONE session per user.** Never log in as the backend automation user or as `chip`. Browser automation (Playwright / Chrome DevTools MCP / headless) counts as a login. Use your own Moraware user or none. This is why BidTracker’s credentialed login + scrape client must **not** be ported.
4. **No unbounded DELETE / UPDATE.** Count first, batch + cap, one transaction per batch, never `.select()` on a bulk delete, never run heavy deletes at boot. (Unbatched delete took prod down 2026-06-24.) Same caution for bulk `UPDATE`.
5. **Test account 2470 only** (“PortalTesting Account”). Never a real account. Goals pipeline drops 2470 unconditionally.

Talk to Chip before anything that reads/writes live company data; default local setup points at production DB/ERP and is wrong for collaborators without scoped access.

---

## Frozen areas (explicit Chip yes required)

| Area | Why |
|---|---|
| COGS logic | Controller-signed; changes reported margins |
| Pricing tiers / price lists / `price_list_items` | Live customer-facing pricing; quartz tariff work in flight |
| Render environment variables | Partial-read / full-write once wiped 46 of 66 keys |
| Home Depot bridge | Hourly unattended writes into HD’s system |
| Scheduled jobs / cron registration | Multi-instance deploys can double-fire |

---

## Canonical systems to REUSE (never bypass)

| System | Rule |
|---|---|
| **Moraware** | Entirely via `backend/` + `tools/moraware-cli` + `azure-moraware-function`. All Moraware reads/writes go through it. Do **not** port BidTracker’s Python client. |
| **Staff commercial / location split** | Only `staff_members.is_commercial` + `staff_members.showroom_location`, routed through `backend/src/services/staffService.ts`. Refs: `docs/patterns/staff-bucket-routing.md`, `docs/references/staff-and-routing.md`. Do not parse crew names, addresses, or customer names. |
| **Auth / users / permissions / portals** | Existing systems are canonical; extend, don’t replace. |
| **Retired commercial estimator** | `backend/src/services/commercialEstimatingService.ts` + `routes/commercialEstimating.ts` (frontend deleted Aug 2026; backend kept for audit). Also read `plans/2026-08-10-commercial-material-prebill-investigation.md`. **Audit first. Do not build on it without Chip’s confirmation.** |

---

## Non-obvious conventions (cost sessions)

- **Multi-phase first-invoice-date pitfall:** commercial jobs invoice in phases over months; several cached tables key on the *first* phase’s invoice date, so later phases go invisible. Gaps that look “close” are bugs — do not round them away. BidTracker’s per-phase model is valuable but must reconcile with this cache assumption.
- **Job number vs jobId:** Moraware job *number* and internal *jobId* are different, both often five digits, not inferable from each other. Always store/write both (e.g. `#20274 (jobId 22476)`).
- **Job Ticket A:** per-phase dollars/SF live on Moraware “Job Ticket A” (one per phase), not on the job header. Blank/zero Invoice TP = zero dollars by design.
- **`GetJob` phases:** returns phases empty unless explicitly requested — silent, not an error.
- **Activity status 12 inverted:** used to mean “Not Ready,” now “Confirmed Ready.” Prefer denylists over allowlists of “active” statuses.
- **Silence ≠ zero:** empty/unread result is not a confident zero — say so.
- **API / plumbing:** `fetchApi()` already adds `/api` (passing `/api/...` doubles it) and returns `{success, data}`; CSRF `Origin` header required on mutations including login; PostgREST **1000-row cap** on `.limit()` and `.range()` (paginate or RPC); two settings tables (`portal_settings` key/value text vs `admin_settings` setting_key/setting_value JSON); React hooks before early returns.

---

## Required reading order (in CounterPro repo)

1. Root `/CLAUDE.md`
2. Nearest-folder `CLAUDE.md` to your work
3. `docs/moraware/INDEX.md` — before any Moraware-touching work
4. `docs/AGENT-PLAYBOOK.md`
5. `docs/PORTAL-FEATURES.md`

### Subagents (`.claude/agents/`)

| Agent | When |
|---|---|
| `repo-cartographer` | Unfamiliar area → short reading list |
| `moraware-oracle` | Any Moraware / CounterGo data read or investigation |
| `db-surgeon` | Supabase query, migration, or cleanup |
| `prod-verifier` | Verifying against live system |

### Guardrails

`.claude/guardrails/rules/` (~30 tripwires). When one fires, **read it** — it quotes an incident. Do not work around it.

---

## PR definition of done

- [ ] `npx tsc --noEmit` passes in `backend/` **and** `frontend/` (frontend build type-checks backend too)
- [ ] `npx vitest run` for touched code
- [ ] No credentials / tokens / connection strings in the diff
- [ ] No migration that deletes or rewrites existing rows without Chip’s explicit sign-off
- [ ] User-visible changes → update `docs/PORTAL-FEATURES.md` (mandatory)
- [ ] PR description states what was verified and how (“it compiles” is not verification)
- [ ] Stage own files explicitly — **never** `git add -A`

Communication: bottom-line first; no multiple-choice menus; honest assessment; flag problems early.

---

## Related handoff docs

- Process: [inspect-first-process.md](inspect-first-process.md)
- Framework: [reuse-extend-map-add.md](reuse-extend-map-add.md)
- Worksheet: [concept-mapping-worksheet.md](concept-mapping-worksheet.md)
- Kickoff prompt: [agent-kickoff-prompt.md](agent-kickoff-prompt.md)
