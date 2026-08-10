# Agent kickoff prompt (copy-paste)

**Bottom line:** Paste the block below into Chip’s CounterPro agent session after the BidTracker `handoff/` package (and preferably the BidTracker repo) is available. It encodes the required 5-step approach, hard rules, and reuse-first bias.

---

```text
You are integrating commercial estimating / bid-management workflows into the Keystone Pricing Portal (CounterPro), using the Keystone Bid Tracker handoff package as REQUIREMENTS + REFERENCE — not as a port spec.

AUTHORITY
- CounterPro’s own CLAUDE.md / docs / guardrails win on all CounterPro matters.
- BidTracker code (`keystone_bid_tracker/`) wins on what BidTracker does today.
- This handoff summarizes BidTracker; it must not override CounterPro systems.
- Do not invent CounterPro table/module names you have not inspected.

REQUIRED 5-STEP APPROACH (in order)
1) Read CounterPro guardrails first: root /CLAUDE.md, nearest-folder CLAUDE.md, docs/moraware/INDEX.md, docs/AGENT-PLAYBOOK.md, docs/PORTAL-FEATURES.md, and .claude/guardrails/rules/.
2) Audit existing CounterPro BEFORE proposing changes — especially:
   - retired commercialEstimatingService.ts + routes/commercialEstimating.ts
   - plans/2026-08-10-commercial-material-prebill-investigation.md
   - staffService.ts (staff_members.is_commercial + showroom_location only)
   - Supabase Moraware-cache tables and backend + moraware-cli + azure-moraware-function
3) Inventory BidTracker concepts from handoff/ + source; fill the REUSE / MAP / EXTEND / ADD worksheet (reuse-first bias). BidTracker HOW (PyQt/SQLite/COM) is reference only.
4) Get Chip’s review before frozen areas, destructive migrations, Moraware writes outside existing paths, or reviving the retired estimator.
5) Implement only what is missing, in CounterPro style (backend Express/TS, database/migrations additive, existing React portals). Never bypass canonical users/permissions/routing/Moraware/staff-split/pricing/COGS.

HARD RULES
- Never push to main (auto-deploys prod; no staging). Branch → fork → PR → Chip merges.
- No production credentials in files or chat requests for service keys.
- Moraware ONE session per user: never automation user or chip; browser automation counts as login.
- No unbounded DELETE/UPDATE; count, batch, cap; never heavy deletes at boot.
- Test Moraware account 2470 only.
- Frozen without Chip yes: COGS, pricing/price_list_items, Render env vars, Home Depot bridge, cron/scheduled jobs.

REUSE-FIRST (anti-duplication)
- Moraware = REUSE existing backend + CLI + Azure Function. NEVER port BidTracker’s Python Moraware client (one-session rule + duplication).
- invoice_data / phases = MAP onto existing Moraware caches; do not parallel-cache.
- Staff commercial routing = REUSE staffService only.
- Audit commercialEstimating first; do not build on it without Chip.
- Likely ADD after audit: bids, revisions, board items, board↔bid links, allocations, parent/child splits, Outlook-sourced board items.
- Outlook: BidTracker Classic COM is a temporary workaround pending Graph admin consent. Graph is intended. For CounterPro (hosted), plan server-side Graph / existing M365 — COM is functional reference only.

PR DoD
- tsc --noEmit backend + frontend; vitest for touched code; no creds in diff; no destructive migrations without sign-off; update docs/PORTAL-FEATURES.md for user-visible changes; stage files explicitly (never git add -A).

Start by reading CounterPro guardrails and auditing the retired commercial estimator + staffService + Moraware caches, then return a filled concept-mapping worksheet (or clear gaps) before writing feature code.
```

---

## Related

- [counterpro-destination-context.md](counterpro-destination-context.md)
- [inspect-first-process.md](inspect-first-process.md)
- [reuse-extend-map-add.md](reuse-extend-map-add.md)
- [concept-mapping-worksheet.md](concept-mapping-worksheet.md)
