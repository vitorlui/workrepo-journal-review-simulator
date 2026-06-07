# Session log / handoff — journal-review-simulator

This folder lets a future "vibe coding" session with Claude **recover full context
and current state** and continue working. Read the files in this order:

1. **[STATE.md](STATE.md)** — current state snapshot: what is built, what works, what is
   pending, how to run it, git/test status, environment facts.
2. **[bitacora.md](bitacora.md)** — chronological logbook of every request the user made
   and what was done for each.
3. **[DECISIONS.md](DECISIONS.md)** — key decisions and approved deviations from the spec
   (the A/B/C improvements, engine-CLI integration, etc.) with rationale.
4. **[CONTINUE.md](CONTINUE.md)** — how to resume: a recap + concrete next steps + a
   ready-to-paste kickoff prompt for the next session.

Source of truth for the *spec* remains `CLAUDE.md` and
`docs/init_plan/prompt_claude_completo_chatgpt.md`. This folder is the *working memory*
of what we actually built and decided.

_Keep these updated at the end of each session._
