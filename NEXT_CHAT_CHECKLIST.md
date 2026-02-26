# NEXT_CHAT_CHECKLIST.md

Use this at the beginning of a new chat.

## 5-Item Preflight

1. Tell the agent to read: `AGENTS.md`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`, `NEXT_CHAT_CHECKLIST.md`, `.cursor/rules/context-first.mdc`.
2. Ask for a 5-bullet summary of current project state.
3. Ask the agent to identify stale/contradictory context before coding.
4. Confirm the exact feature/bug scope in one sentence.
5. Ask for the proposed `SESSION_NOTES.md` entry at session end.

## Starter Prompt (copy/paste)

Before we start, read `AGENTS.md`, `PROJECT_CONTEXT.md`, `SESSION_NOTES.md`, and `NEXT_CHAT_CHECKLIST.md` in the repo root, plus `.cursor/rules/context-first.mdc`. Then give me:

1. a 5-bullet summary of current project state,
2. any stale/contradictory context you found,
3. the proposed update (if needed) to `SESSION_NOTES.md` for this session.

Do not code yet; wait for my feature request after your summary.
