# Other PC handoff

**Purpose:** One short “here’s what I did before I pushed” note so your **other machine** and the **next Cursor chat** start aligned. This is **not** a full history—that’s `SESSION_NOTES.md`.

## How to use

1. **Before you push** (or right after, same session): edit **Current handoff** below. Keep it to a few bullets.
2. **On the other PC:** run `git pull`, then **open this file** (and `SESSION_NOTES.md` if you need detail).
3. **Overwrite** the handoff each time you push meaningful work—don’t grow this into a diary.

## On the other machine after `git pull`

- [ ] Read **Current handoff** (this file).
- [ ] Skim the latest entry in `SESSION_NOTES.md` if you need timestamps/commits.
- [ ] `.venv` is local-only: if `requirements.txt` changed, recreate or `pip install -r requirements.txt` inside `.venv`.
- [ ] `keystone_bid_tracker/config.json` is still **not** in git—each PC keeps its own paths/credentials.

---

## Current handoff

**Last updated:** 2026-08-10  
**Branch:** `main`

**What I did:**

- Shipped Bid Board + Outlook read-only sync + CounterPro `handoff/` docs (commit `433dc17`).
- Pushed `origin/main` and mirrored to private Chip repo: https://github.com/ATFROMKC/Keystone-Bid-Tracker-Handoff (git remote `chip-handoff`).

**Heads-up for the other PC:**

- **`git pull`** on `main`.
- `requirements.txt` changed — run `pip install -r requirements.txt` in `.venv`.
- Still do **not** commit `config.json`. Local excludes remain: PDF / `_tmp_eids.json` / `outlook_com_poc.py`.

**Open questions / none**

- Invite Chip (GitHub username) as Read collaborator on the handoff repo if not done yet.
