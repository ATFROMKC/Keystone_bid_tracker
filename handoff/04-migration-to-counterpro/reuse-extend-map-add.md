# Reuse → Map → Extend → Add

**Bottom line:** Prefer reuse. The main failure mode is rebuilding a capability CounterPro already has because BidTracker has a desktop screen for it. BidTracker implementation is **reference for requirements**, not a template to copy.

Classify every concept only after inspecting CounterPro (see [inspect-first-process.md](inspect-first-process.md)). Fill [concept-mapping-worksheet.md](concept-mapping-worksheet.md).

---

## Definitions (decision order)

### 1. Reuse (preferred)

CounterPro already has an equivalent system. Wire BidTracker **business rules** onto it; build nothing parallel.

**Examples (hypotheses — verify):**

- **Moraware jobs / sync / ERP reads** → Reuse `backend/` + `tools/moraware-cli` + `azure-moraware-function`
- **Staff commercial / location routing** → Reuse `staff_members.is_commercial` + `showroom_location` via `staffService.ts`
- **Auth / users / permissions / portals** → Reuse existing systems

### 2. Map

Same idea under a different CounterPro name or shape. Translate identities and fields; do not recreate the entity.

**Examples (hypotheses — verify):**

- BidTracker `invoice_data` / phases → Map onto existing Supabase Moraware-cache tables (jobs / activities / phases / invoicing). Extend only if fields are missing; **never** a parallel invoice cache.
- BidTracker estimator roster ↔ CounterPro staff/auth identities (tie people; don’t invent a second user system)

### 3. Extend

CounterPro has a close entity missing a few fields or behaviors. Add columns, routes, or UI additively. Respect cache/sync assumptions and frozen areas.

### 4. Add (last resort)

No CounterPro equivalent after a real audit. Build new in CounterPro’s idiom (Express services, `database/migrations/`, existing portal UI), using BidTracker **rules and invariants** as requirements.

**Likely Add candidates after audit (verify):** bids, revisions, bid-board opportunities, board↔bid links, allocations, parent/child split bids, Outlook-sourced board items (Graph server-side). These are mostly non-Moraware commercial estimating surfaces.

---

## Decision rules

| Question | If yes → |
|---|---|
| Does CounterPro already own this truth (esp. Moraware / staff / auth / pricing)? | **Reuse** (or Map onto its cache) |
| Is this the same concept with different naming? | **Map** |
| Is there a close table/service missing 1–N fields? | **Extend** |
| After audit, nothing covers the BidTracker invariant? | **Add** |
| Would this create a second Moraware client or invoice cache? | **Stop** — Reuse/Map instead |
| Is the area frozen (COGS, pricing, Render env, HD bridge, cron)? | **Chip yes** before any change |

---

## Failure mode

**Rebuilding existing CounterPro capability** — e.g.:

- Porting BidTracker’s Moraware Python client (also breaks one-session-per-user)
- Standing up a new commercial estimator without auditing `commercialEstimatingService.ts`
- Deriving commercial vs residential from job names/addresses instead of `staffService`
- Parallel Supabase tables that re-cache Moraware phases/invoices

Suggesting BidTracker’s approach is fine. Shipping a redundant system is not.

---

## BidTracker HOW vs WHAT

| Treat as | Content |
|---|---|
| Authoritative | WHAT / WHY: statuses, links, allocations must sum, WON not deletable, board COMPLETE ≠ bid WON, dual Moraware IDs, Outlook read-only upsert rules |
| Reference only | HOW: PyQt dialogs, SQLite schema shape, Dropbox paths, Classic Outlook COM |

Implement Adds/Extends in CounterPro style even when BidTracker’s approach “works.”
