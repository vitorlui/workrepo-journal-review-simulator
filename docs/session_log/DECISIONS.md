# Decisions & approved deviations

Decisions made with the user, so the next session doesn't re-litigate them.

## Initial choices (plan mode)
- **Frontend:** Next.js (App Router) + Tailwind. (vs React/Vite)
- **MVP pipeline:** offline **`template`** engine — deterministic Markdown scaffolds with a
  pluggable LLM seam. Runs with no API keys. (vs wiring live LLMs from day one)
- **Language:** English for UI + README (venue/reviewer content already English).

## Approved deviations from the literal spec (A + B + C)
The user explicitly asked NOT to follow the spec blindly and approved all of these:

- **A1 — Stable venue IDs:** slug from acronym/name (e.g. `data-in-brief`), **not** the raw
  `V#`. The two Perplexity batches reuse `V21/V22` for different journals → literal IDs would
  overwrite. Original `V#`+file kept as `source_ref`. (Collision → numeric suffix, e.g. `dib-2`.)
- **A2 — Filenames without `*`:** `<review_id>__<venue_id>__rev{n}_<profile>_<engine>_response.md`
  (the spec's `*` is a glob wildcard / invalid on Windows).
- **B3 — MIME via pure-Python `filetype`** + mimetypes (no libmagic) → works natively on Windows.
- **B4 — SQLite fallback** when `DATABASE_URL` unset (Postgres in Docker).
- **B5 — `pathlib` everywhere + `.gitattributes` (LF).**
- **C6 — `worker/` is the single core library** (API + scripts import it; no triplication).
- **C7 — pipeline runs in-process** (no queue) for the MVP; `worker` container for CLI.
- **C8 — one canonical reviewer-profile source** in `data/global_knowledge/reviewer_profiles/`;
  `.claude/agents/*.md` reference it (no duplicated rubric).
- **C9 — `db/schema.sql` generated** from the ORM models (`scripts/dump_schema.py`); models canonical.
- **D10 — PDF export best-effort:** Markdown always; PDF only if a renderer is present (Docker).

## Engine CLI integration (later request)
- **CLI over browser automation / HTTP APIs.** The user wants a worker that runs the **local
  CLI** of each tool with our generated prompt. Rationale: no API keys, no ToS risk, uses the
  plans they already have. Browser automation of LLM web UIs was explicitly **rejected**.
- **Engines:** `claude` (Claude Code), `codex` (ChatGPT via Codex CLI), `gemini` (Gemini CLI
  free tier), `ollama` (local). **Perplexity omitted** (no CLI / tokens exhausted).
- **Cost stance:** must use only existing plans — Claude Max, ChatGPT Pro (covers Codex),
  Gemini free tier (Google login, no Pro), Ollama local. **No extra purchases.**
- **Command templates live in `config/model_config.yaml` → `cli_engines`** (editable without code).
- **Deployment for this feature:** backend must run **natively on the host** (Docker can't reach
  host CLIs / cached logins). `scripts/dev_native.ps1` is the launcher.

## Git workflow
- Work committed on **`feat/mvp-scaffold`** (branch-first off the default branch).
- Merge to `master` is the recommended next git action (validated work; solo repo).
