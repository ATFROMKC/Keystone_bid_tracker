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

**Last updated:** 2026-03-24  
**Branch:** `main`

**What I did:**

- Added **`OTHER_PC_HANDOFF.md`** and wired it into **`AGENTS.md`**, **`PROJECT_CONTEXT.md`**, **`NEXT_CHAT_CHECKLIST.md`**, **`.cursor/rules/context-first.mdc`**, **`.cursor/rules/git-session-sync.mdc`** (session-end step 6: offer to refresh this file when pushing).
- Remote `main` also has launcher diagnostics (`scripts/launch_app.py`, debug `.cmd`); see latest `SESSION_NOTES.md` if launch issues persist.

**Heads-up for the other PC:**

- **`git pull`** on `main`. Read this file after pull.
- If **`requirements.txt`** didn’t change, existing `.venv` is usually fine; if launch fails, ensure **`.venv\Scripts\pythonw.exe`** exists or use **`launch_keystone_bid_tracker_debug.cmd`** to see errors.

**Open questions / none**

- (Add anything the other machine should know that isn’t obvious from the diff.)
