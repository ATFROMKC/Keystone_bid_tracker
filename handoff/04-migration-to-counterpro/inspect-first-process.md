# Inspect-first process

**Bottom line:** Do not design BidTracker-into-CounterPro features until you have read CounterPro’s guardrails and audited what already exists (especially the retired commercial estimator, `staffService`, and Moraware caches). Anti-duplication is the primary guardrail. BidTracker’s HOW is reference, not a template.

CounterPro’s own docs win on CounterPro matters — see [counterpro-destination-context.md](counterpro-destination-context.md).

---

## Step 1 — Read CounterPro guardrails

In the **CounterPro / Keystone Pricing Portal** repo, in order:

1. Root `/CLAUDE.md`
2. Nearest-folder `CLAUDE.md` to the area you will touch
3. `docs/moraware/INDEX.md` (before any Moraware work)
4. `docs/AGENT-PLAYBOOK.md`
5. `docs/PORTAL-FEATURES.md`
6. Skim `.claude/guardrails/rules/` for what fires on deletes, credentials, double `/api`, CSRF, broad `git add`, push-to-main

Use subagents when appropriate: `repo-cartographer`, `moraware-oracle`, `db-surgeon`, `prod-verifier`.

---

## Step 2 — Audit existing CounterPro surfaces FIRST

Before proposing BidTracker-like tables, routes, or UI:

| Priority | Inspect | Why |
|---|---|---|
| 1 | `commercialEstimatingService.ts` + `routes/commercialEstimating.ts` + `plans/2026-08-10-commercial-material-prebill-investigation.md` | Retired commercial estimator — highest-value anti-duplication check. Confirm direction with Chip before building on or beside it. |
| 2 | `backend/src/services/staffService.ts` + staff-bucket docs | Commercial vs residential / KC vs Wichita routing is canonical here. |
| 3 | Supabase Moraware-cache tables + sync paths (`backend/` + `moraware-cli` + `azure-moraware-function`) | Do not create a parallel Moraware/invoice cache. Map BidTracker `invoice_data` / phases onto existing caches. |
| 4 | Auth, users, permissions, portals | Extend; do not replace. |
| 5 | Existing reporting / Goals / PM-adjacent surfaces | Avoid a second source of “truth” for the same metrics. |

**Failure mode to avoid:** rebuilding something CounterPro already provides because BidTracker has a PyQt screen for it.

---

## Step 3 — Inventory BidTracker concepts

Use this handoff package + live BidTracker source:

- Orientation: `handoff/00-orientation/`
- Data model: `handoff/01-data-model/` + `keystone_bid_tracker/database.py`
- Workflows: `handoff/02-workflows/`
- Integrations: `handoff/03-integrations/` (Moraware = **behavior reference only**; do not port the client)
- Gaps: `handoff/05-known-gaps.md`

Capture WHAT / WHY (rules, relationships, invariants). Treat HOW (PyQt, SQLite paths, COM) as optional comparison.

---

## Step 4 — Fill the worksheet (REUSE / EXTEND / MAP / ADD)

Complete [concept-mapping-worksheet.md](concept-mapping-worksheet.md) for every concept.

Bias order (see [reuse-extend-map-add.md](reuse-extend-map-add.md)):

1. **Reuse** (preferred)
2. **Map**
3. **Extend**
4. **Add** (last resort)

Default hypotheses in the worksheet are starting points — **verify by inspecting CounterPro**, then overwrite.

---

## Step 5 — Chip review before destructive or conflicting work

Get Chip’s explicit yes before:

- Anything in a **frozen** area (COGS, pricing / `price_list_items`, Render env vars, Home Depot bridge, cron)
- Migrations that delete or rewrite existing rows
- Moraware writes outside existing backend paths
- Reviving or building on the retired commercial estimator
- Parallel caches or shadow staff/auth routing

Non-destructive audits and worksheet drafts do not need this gate; conflicting or destructive changes do.

---

## Step 6 — Implement in CounterPro style

Only after steps 1–5:

- Business logic → `backend/` Express + TypeScript services
- Schema → additive files in `database/migrations/`
- UI → existing React 18 + TS + Vite portal conventions (likely Admin / field)
- Moraware → call existing backend/cli/Azure paths only
- Outlook → server-side Graph / existing M365 (COM is BidTracker workaround reference only)
- Follow PR DoD in [counterpro-destination-context.md](counterpro-destination-context.md)

---

## Anti-duplication checklist (keep visible)

- [ ] Did not port BidTracker’s Moraware client
- [ ] Audited retired commercial estimator and confirmed direction with Chip
- [ ] Did not create a second Moraware / invoice / phase cache
- [ ] Staff commercial routing goes through `staffService` / `staff_members` only
- [ ] Users/auth/permissions extended, not shadowed
- [ ] Every concept classified on the worksheet before coding
- [ ] BidTracker UI patterns treated as reference, not copy targets
