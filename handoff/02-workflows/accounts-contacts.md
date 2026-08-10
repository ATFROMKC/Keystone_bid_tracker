# Accounts & contacts

**Bottom line:** Accounts (`customers`) and reusable email contacts (`customer_contacts`) are shared master data. Bid account links (`bid_customers`) and board account links (`bid_board_item_customers`) are **independent**. Inactive accounts stay in history but are hidden from new pickers unless already linked. Merging reassigns all FK references and deletes the source account.

> **Framing:** WHAT / WHY is authoritative. PyQt account tabs are reference only.

---

## WHAT / WHY (business rules)

### Accounts

- An **account** is a company/customer row in `customers` (display name + `active` flag).
- Accounts appear on:
  - **Bids** via `bid_customers`
  - **Board items** via `bid_board_item_customers`
  - **Won award** via `bids.won_customer_id` (must be one of / addable to the bid’s accounts)

These link tables are **not synchronized automatically**. Linking an account on a board card does not attach it to a later logged bid unless the log dialog copies those IDs (BidTracker’s log-bid flow typically prefills from the card’s accounts, but after creation the join sets diverge freely).

### Contacts

- **Contacts** are emails (+ optional name) owned by an account (`customer_contacts`).
- Board items pick a **subset** of contacts for invite/recipients via `bid_board_item_contacts`.
- Contacts are reusable across board items; they are not bid revisions or Moraware entities.
- Contact `active` can be filtered when listing for pickers.

### Active vs inactive

| Rule | Behavior |
|---|---|
| Inactive accounts | Hidden from **new** account pickers (`get_customers(active_only=True)`) |
| Already linked inactive | Still shown / kept when editing a bid or board item that already has them |
| Toggle inactive | Soft-hide; does not delete history or unlink existing joins |

### Merge accounts

`merge_customers(merge_from_id, merge_into_id)` side effects:

1. Reassign `bid_customers` from → into; dedupe `(bid_id, customer_id)`.
2. Reassign `bid_board_item_customers` from → into; dedupe `(board_item_id, customer_id)`.
3. Reassign `bids.won_customer_id` from → into.
4. Move contacts: if email already exists on the kept account, re-point board contact links to the kept contact and delete the duplicate; otherwise move the contact row.
5. **Delete** the merge-from `customers` row.

Merge is destructive for the source account identity; preserve audit expectations accordingly in CounterPro.

---

## HOW BidTracker does it (reference)

| Concern | Path |
|---|---|
| Accounts list / add / active / merge UI | `ui/customers_tab.py` |
| Edit name + manage contacts | `ui/edit_account_dialog.py` |
| CRUD / merge / bid & board customer helpers | `database.py` → `add_customer`, `get_customers`, `merge_customers`, `get_bid_customers`, `get_board_item_customers`, contact helpers |
| Bid picker keeps inactive-if-linked | `ui/add_bid_dialog.py` → `_load_customers` |
| Board dialog account/contact pickers | `ui/bid_board_item_dialog.py` |
| Mark Won may insert won account onto bid | `ui/mark_won_dialog.py` |

---

## Invariants to preserve in CounterPro

1. Bid account links ≠ board account links (two join tables / equivalent).
2. Inactive = hidden from discovery, not erased from history.
3. Merge rewrites won-customer, bid links, board links, and contacts atomically.
4. Contacts are account-owned reusable emails, optionally selected per board opportunity.
