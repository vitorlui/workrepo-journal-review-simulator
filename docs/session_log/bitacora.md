# Bitácora — chronological log of requests & changes

Session date: **2026-06-07**. Branch: **`feat/mvp-scaffold`** (off `master`).
User: Dr. Vítor da Silva. Builder/orchestrator: Claude (Claude Code, Opus 4.8).

Each entry = a user request + what was done.

---

## 1. Build the first functional MVP
**Request:** Build the first working version of `journal-review-simulator` following
`docs/init_plan/prompt_claude_completo_chatgpt.md` + `CLAUDE.md`: architecture, Docker Compose,
frontend, backend, documental structure, DB, pipeline, importers, subagents, skills, templates.
Perplexity venue answer not fully ready → create `data/global_knowledge/venue_discovery/{raw,processed,import_reports}/`,
**import what we already have**, and a script/endpoint to import future Perplexity MD/CSV.

**Done (plan mode):** explored the spec, asked 3 questions →
**Next.js (App Router)**, **offline template pipeline with LLM seam**, **English UI/README**.
Wrote the plan to `~/.claude/plans/`.

## 2. "Don't follow the spec literally — propose better changes"
**Request:** Review the spec critically and show only what I would change.
**Done:** Proposed deviations **A (correctness)**, **B (Windows/DX)**, **C (architecture)** +
PDF best-effort. User approved **all (A+B+C)** and **best-effort PDF**. See `DECISIONS.md`.

## 3. Implementation of the MVP
**Done:** Built the whole MVP (see `STATE.md` for the file map):
- `config/*.yaml`, `worker/` core library, `worker/venue_discovery.py` importer, DB
  (`worker/db.py` + generated `db/schema.sql` + seed), FastAPI app + routers, `scripts/*`,
  13 reviewer profiles + 18 `.claude/agents` + integrity skill + templates, Next.js UI
  (sidebar + 13-step wizard), Dockerfiles + `docker-compose.yml`, `README.md`.
- **Imported the two bundled Perplexity files → 37 venues** on disk (22 from the Markdown
  table + 15 from the messy CSV; 1 collision auto-resolved as `dib-2`). Fixed two real
  importer bugs: unbalanced-quote CSV rows and cp1252/utf-8 decoding.
- Verified: `check_structure` 57/57, importer, full pipeline smoke (review → extract →
  classify → reviewers → editor → export), FastAPI via TestClient.

## 4. "We have a git repo — validate, test, commit. If no tests, create tests."
**Done:** Wrote a **pytest suite (23 tests)** isolated in a temp DATA_DIR (worker core,
venue importer, pipeline e2e, API). Fixed `datetime.utcnow()` deprecations. All green.
**Committed the MVP** on `feat/mvp-scaffold` → **`a7ab4d9`** (484 files).
(Branch-first per the default-branch guideline; merge to `master` pending user OK.)

## 5. "Docker Desktop started"
**Done:** Built all images — **web 1.01 GB, api 459 MB, worker 459 MB** (`docker compose build` OK).
(`docker compose config` had already validated; the daemon was down earlier.)

## 6. Playwright + Codex idea → CLI engine integration
**Request (clarified):** Test our web with Playwright; and for the manual "search in LLMs"
step, a **worker that runs the CLI** of Codex (ChatGPT) / Claude / Ollama / Gemini with our
generated prompt, triggered by an **"Execute query" button**. Perplexity later (tokens out).
**Done:**
- `worker/engines/` — `CliEngine` (config-driven), registry, `run_query`, `engine_status`
  (+ optional HTTP adapters kept). `config/model_config.yaml` → `cli_engines` + `query_engines`.
- `worker/run_query.py` + `external_responses.save_generated_response` +
  `external_prompt_manager.build_execution_prompt`.
- API: `POST /reviews/{id}/run-query`, `GET /engine-status`.
- UI: **Execute query** control in wizard step 7 (venue + reviewer + engine, availability-aware).
- **Playwright E2E** (`apps/web/e2e/` smoke + review-flow) + **9 engine tests** (mocked
  subprocess) → **32 pytest total**. Verified live: `claude -p` actually ran from the worker.
- **Committed** → **`fde22d3`**.

## 7. "How to integrate Gemini without paying Pro?"
**Answer:** No extra cost. Claude→Claude Max, ChatGPT→Codex CLI (sign in with ChatGPT Pro),
**Gemini→Gemini CLI free tier with a Google login (no Pro, no API key)**, Ollama→local.

## 8. "Install Gemini and Codex if not present"
**Done:** Node/npm were missing. Installed **Node.js LTS via winget** (v24.16.0), then
`npm i -g @openai/codex @google/gemini-cli`. Both at `%APPDATA%\npm\{codex,gemini}.cmd`
(on PATH in new terminals). Auth is a one-time login per CLI.

## 9. "Document in the README how to run/configure the CLIs on our host"
**Done:** Added README **"Host setup — run the CLIs from your own computer"** (install + auth
table, native launcher, web UI vs no-frontend usage). Added `scripts/dev_native.ps1`
(native API, SQLite fallback, prints engine availability) and `scripts/run_query.py`
(run a query / `--status` with no frontend).

## 10. "Create a logbook; document everything to continue the session; in a dedicated folder"
**Done:** This `docs/session_log/` folder (`README`, `STATE`, `bitacora`, `DECISIONS`, `CONTINUE`).
Committed `b94c84d`; **merged `feat/mvp-scaffold` → `master`** (ff). `master` ahead of
`origin/master` by 3 (not pushed — user only asked to commit).

## 11. "Continue with the recommended next step"
**Done:** Wired the engine CLIs into the **internal pipeline**. `worker/agent_orchestrator.py`
now runs the real CLI (`claude`/`codex`/`gemini`/`ollama`) for reviewers, the integrity audit and
the editor when `PIPELINE_ENGINE` names a real engine, with **offline template fallback** if the
CLI is missing/errors. Added prompt builders (`_integrity_prompt`, `_editor_prompt`; reviewers
reuse `build_execution_prompt`). 4 new tests (engine path used / fallback / editor / template
default) → **36 pytest pass**. Updated STATE.md + CONTINUE.md.

---

### Pending after this entry
- Optional: `git push` (master ahead of origin by 4 after this commit).
- Run Playwright E2E; do a real-engine full_review; see `CONTINUE.md`.
