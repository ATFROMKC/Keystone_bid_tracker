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

**Last updated:** 2026-03-23  
**Branch:** `main`

**What I did:**

- Added `OTHER_PC_HANDOFF.md` and wired it into `AGENTS.md`, `NEXT_CHAT_CHECKLIST.md`, `.cursor/rules/context-first.mdc`, and `.cursor/rules/git-session-sync.mdc` so agents read a short multi-PC note after `SESSION_NOTES.md`.
- (Earlier on `main`: Windows launcher with `start ""`, desktop shortcut script, taskbar AppUserModelID, `.venv/` gitignored—see `SESSION_NOTES.md`.)

**Heads-up for the other PC:**

- `git pull` on `main`. If `requirements.txt` didn’t change, your existing `.venv` is fine.
- If launch `.cmd` fails: ensure `.venv\Scripts\pythonw.exe` exists (`py -3 -m venv .venv` + `pip install -r requirements.txt`).

**Open questions / none**

- (Add anything the other machine should know that isn’t obvious from the diff.)
