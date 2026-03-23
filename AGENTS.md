# AGENTS.md

## Purpose

This file is the stable operating contract for AI assistants and humans working in this repo.

## Required Startup Behavior

At the start of every new chat/session, read these files first (if present):

1. `AGENTS.md`
2. `PROJECT_CONTEXT.md`
3. `SESSION_NOTES.md`
4. `NEXT_CHAT_CHECKLIST.md`
5. `.cursor/rules/context-first.mdc`
6. `.cursor/rules/git-session-sync.mdc`

Then provide a short understanding summary before coding.

## Source of Truth Order

When there is conflicting guidance, use this order:

1. Actual code in `keystone_bid_tracker/`
2. `PROJECT_CONTEXT.md` (current architecture/decisions)
3. `SESSION_NOTES.md` (recent work log)
4. Legacy docs such as `HANDOFF.md`

## Scope and Change Guardrails

- Keep changes focused to the request; avoid broad refactors unless explicitly asked.
- Do not rename/move files as cleanup-only work unless explicitly asked.
- Prefer additive, reversible edits over risky rewrites.
- Flag stale or conflicting docs before relying on them.

## Git and Safety Hygiene

- Never run destructive git commands unless explicitly approved.
- Do not commit or push **except** when the user requests it **or** when following **`.cursor/rules/git-session-sync.mdc`** (session-end sync: status → stage → commit → push → `SESSION_NOTES.md`).
- If unrelated local changes exist, do not revert them.

## End-of-Session Requirement

Follow **`.cursor/rules/git-session-sync.mdc`**:

- **Session start:** remind (or run) **`git pull`**.
- **Session end:** when the user wraps up or asks to sync/push, run **`git status`**, stage, commit (user message or assistant-proposed summary), **push to GitHub**, and **append a dated entry to `SESSION_NOTES.md`** unless the user opts out of notes.

If the user only wants a minimal note without git operations, you may still ask: "should I append a concise entry to `SESSION_NOTES.md` only (no commit)?"
