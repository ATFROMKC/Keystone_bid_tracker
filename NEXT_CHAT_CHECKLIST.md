# NEXT_CHAT_CHECKLIST.md

Use this at the beginning of a new chat.

## 5-Item Preflight

1. Tell the agent to read: `AGENTS.md`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`, `NEXT_CHAT_CHECKLIST.md`, `.cursor/rules/context-first.mdc`.
2. Ask for a 5-bullet summary of current project state.
3. Ask the agent to identify stale/contradictory context before coding.
4. Confirm the exact feature/bug scope in one sentence.
5. At session end, ask exactly: "should I append a concise entry to session_notes.md?" and append only if I say yes.

## Session Operator Lines (add after preflight)

Use these to keep scope focused while capturing surprise ideas:

- If I mention a new idea, treat it as `PARK` unless I explicitly say `SWITCH`.
- `MICRO` changes are allowed only if under 10 minutes and no schema/architecture impact.

## Starter Prompt (copy/paste)

Before we start, read `AGENTS.md`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`, and `NEXT_CHAT_CHECKLIST.md` in the repo root, plus `.cursor/rules/context-first.mdc`. Then give me:

1. a 5-bullet summary of current project state,
2. any stale/contradictory context you found,
3. how you will handle `SESSION_NOTES.md` at close by asking exactly: "should I append a concise entry to session_notes.md?" and appending only if I say yes.

Do not code yet; wait for my feature request after your summary.
