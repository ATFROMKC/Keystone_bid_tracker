# Sequencing (optional)

**Bottom line:** Phases below are a **non-binding suggestion** only. Chip’s priorities, frozen areas, and CounterPro’s own roadmap override this list. Always run the inspect-first audit before coding.

This is **not** a project plan or commitment.

---

## Optional suggested phases

| Phase | Focus | Intent |
|------:|---|---|
| 0 | **Audit** retired commercial estimator + `staffService` + Moraware caches | Highest anti-duplication value; confirm direction with Chip |
| 1 | **Map** Moraware / invoice / phases onto existing caches | Reuse Moraware stack; no parallel cache; note multi-phase pitfall |
| 2 | **Add** bid core (bids, revisions, statuses, accounts linkage as needed) | Genuine Add after audit |
| 3 | **Add** Bid Board (opportunities, board↔bid links, colors/status rules) | Orthogonal board vs bid lifecycles |
| 4 | **Add/Extend** PM overlays (Active Jobs link overlay, Pending Award, splits/allocations) | Moraware list = Reuse; local overlays = Add |
| 5 | **Add** Outlook via **Graph** server-side | COM = BidTracker workaround reference only |
| 6 | **Reports** / pipeline / history UI | Reuse portal reporting where possible; fill known BidTracker UI gaps carefully |

---

## Constraints that apply in every phase

- Never push `main`; no prod credentials; Moraware one session; no unbounded DELETE/UPDATE; test account **2470** only
- Frozen areas need Chip yes
- BidTracker HOW is reference; implement in CounterPro style
- Fill [concept-mapping-worksheet.md](concept-mapping-worksheet.md) before each Add

---

## Explicitly optional

Skip, reorder, or collapse phases as CounterPro inspection warrants. If audit shows the retired estimator (or another surface) already covers a phase, **Reuse/Map/Extend** instead of Add — that is a successful outcome, not a skipped deliverable.
