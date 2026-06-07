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

## 12. "Help button" + "run a+b, watch Playwright slowly, paper by paper"
**Done:**
- **Help button**: floating `?` with a step-by-step guided tour (auto-opens on first visit).
  Commit `94b72f6`.
- **(a) Pushed** `master` to `origin` (github.com/vitorlui/workrepo-journal-review-simulator).
- **(b) Visible Playwright demo** over the user's real papers, paper by paper:
  - The user's papers weren't attachable to the workspace; located them in `Downloads` and copied
    `PAPER_A_dataset.pdf`, `PAPER_B_compag.pdf`, `PAPER_C_cosine.pdf` into `apps/web/e2e/papers/`
    (the "Ángel" wheat paper was excluded per the user).
  - Brought the stack up natively, ran `paper-runs.spec.ts` **headed + `PW_SLOWMO=700`** →
    **3 passed**; each paper visibly: create review → upload → extract → classify → venues.
  - Classification on the real PDFs looked right (A=data descriptor, B=benchmark/agri-food, C=survey).
- **Gotchas solved (record for next time):**
  1. **`:3000` was taken by OpenWebUI** → ran the web on **`:3001`** (`next dev -p 3001`).
  2. **CORS**: API default allowed only `:3000`; the browser on `:3001` was blocked. Fixed live via
     `CORS_ORIGINS`, and **permanently** with `allow_origin_regex` for any localhost port in `main.py`.
  3. **Chromium download was AV-blocked** (download hit 100% but `chrome.exe` never extracted, leaving a
     stale `__dirlock`). Worked around with **`PW_CHANNEL=msedge`** → use the installed Edge (config now
     reads `PW_CHANNEL`). No browser download needed on Windows.
  4. Playwright **strict-mode**: assertions must match one element (used `.first()` / specific roles).
- 36 pytest still pass. The 3 demo reviews remain under `data/reviews/` (gitignored) — ready to run
  the full reviewer/editor pipeline on, optionally with a real engine.

## 13. Real-engine run on PAPER_A (claude) + bug fixes
**Done:**
- Ran `full_review` with `PIPELINE_ENGINE=claude` on PAPER_A. The **integrity audit and editor
  ran real (claude-sonnet-4-6)** and produced excellent, rule-respecting content (the editor even
  refused to invent findings and flagged a venue mismatch — JMLR auto-selected for a wheat/DON paper).
- **Two real bugs found & fixed** (commit `62c7a17`):
  1. **PDF field extraction**: raw text extracted fine (16 KB) but structured fields were all
     `NEEDS_USER_INPUT` because the parser only read Markdown `#` headings. Added a fallback:
     title = first line, abstract = text after the "Abstract" keyword. PAPER_A now extracts a real
     title/abstract.
  2. **`claude -p` stdin race**: piped `input=` made `claude -p` abort after a 3s stdin wait →
     reviewers fell back to template. Fixed by feeding a **temp-file stdin handle**. Verified live.
- **Known limitation (important):** running `claude -p` **nested inside this Claude Code session**
  is flaky — the *first* call tends to hang to the 600s timeout, and a long 10-call run **died at
  3/8** (process vanished, no traceback). 2 reviewers came out real (domain, systems).
  **Recommendation:** for full real runs use a **separate-process engine — `codex` (ChatGPT Pro,
  needs one-time `codex` login) or `ollama` (local)** — not nested claude. User chose to keep the
  2 real claude reviews as-is for now.
- 36 pytest pass throughout.

## 14. Live real-engine review + UI/UX hardening (same day, long session)
All pushed to `origin/master` (latest commit `b03afad`). Highlights:

- **Default reviewers:** 3 core (methodology, domain, reproducibility) → then **4** after the user asked
  to include systems-architecture. `_main_reviewers()` honours `default_enabled`. Specialized still
  auto-activate by area; scientific-impact is optional. (commits `62a90da`, `c8346c9`)
- **Completed status:** pipeline now writes `status`/`current_step` (+ parsed final decision) to
  `metadata.yaml`, so the UI shows reviews as completed (was always "created"). (`39c63ba`)
- **Results view (step 11):** `GET /reviews/{id}/summary` + `worker/summary.py` digest each reviewer's
  recommendation + the editor decision; the wizard shows a colored decision banner + a reviewer table +
  rendered Markdown (`react-markdown` + `remark-gfm`, `components/Markdown.tsx`). (`002c96d`)
- **Double-confirm** before regenerating a completed review. (`b070993`)
- **REAL engine demo (the big one):** installed Node + `@openai/codex` + `@google/gemini-cli`. Ran
  `PIPELINE_ENGINE=claude full_review` on PAPER_A (the wheat/DON NIR-HSI paper). Found+fixed: PDF field
  extraction (title/abstract fallback), `claude -p` stdin race (temp-file stdin), editor decision
  parsing. **Demonstrated end-to-end**: against **JMLR** → editor **DESK REJECT** (scope mismatch, redirect);
  re-ran against the correct venue **Scientific Data** → 7 real claude reviewers (all *major revision*) →
  editor **MAJOR REVISION**. Proves venue choice drives the decision and that agents really run.
  (`62c7a17`, `e01ec64`)
- **Playwright E2E with the user's papers:** copied PAPER_A/B/C from Downloads into `apps/web/e2e/papers/`,
  ran headed + slow on **Edge** (`PW_CHANNEL=msedge`, Chromium download was AV-blocked) → 3 passed.
- **Charset fix:** `cli_engine` decoded CLI output as cp1252 on Windows → mojibake (`â€"`). Fixed: decode
  UTF-8 explicitly + `ftfy` safety net + repaired existing files. (`d83467e`)
- **Live status:** running panel (spinner + elapsed + ETA + progress bar) + browser notification on
  finish + per-step `running:*` status; auto-refresh poll (4s) bumps a tick so panels self-update,
  even for CLI-triggered runs. (`c3fde89`)
- **Area over-detection fix:** keyword matching was substring-based (`cer`∈`cereal`, `don`∈`done`) →
  whole-token matching + ≥2-keyword threshold + cap 3 areas. (`192817d`)
- **Venue discovery UI:** ranked candidates (relevant first, green score badge, dim non-matches,
  show-all toggle) via `GET /reviews/{id}/venue-candidates`; **repaired 6 venues** whose `venue_family`
  was mangled by inconsistent Markdown-table cells (c-e, cea, cviu, eait, tlt, toce). (`7676910`)
- **Next-step button + dimmed pending steps** (done detected by artifact existence, `isStepDone`). (`7676910`, `be8556e`)
- **Save-selection fix** (auto-refresh was wiping checkboxes). (`b920dc1`)
- **Artifact panel hardening** (never blanks on error, self-heals, empty-state hint; silent poll errors). (`4320b74`)
- **NEEDS_USER_INPUT → "pending"** in the UI (data keeps the token); strip literal `**`. (`c3fde89`)
- **Auto-identified metadata:** title is taken from the extracted manuscript (classify step). Step 0 is a
  clean read-only summary (the review is created on "New Review"; Upload is the real first action). (`c3fde89`)
- **Desk-reject precheck made real:** deterministic findings from the extraction (missing references,
  no experiments, no data/code statement, no area) + verdict — no longer a blank NEEDS_USER_INPUT scaffold. (`b03afad`)
- **Honest architecture note (user asked):** deterministic parts are REAL (extraction, classification,
  venue ranking, desk-reject). Reviewers/integrity/editor are **template scaffolds by default** but
  **really run the agent CLI** when `PIPELINE_ENGINE` is a real engine (proven on PAPER_A). The **web API
  runs `template` by default** → browser "Run" buttons give scaffolds unless the API is started with
  `PIPELINE_ENGINE=claude|codex`.

---

### Standby — 2026-06-07 (resuming ~2026-06-09)
Working tree clean, `master` == `origin/master` @ `b03afad`. See `STATE.md` for the snapshot and
`CONTINUE.md` for exactly how to restart the servers and what to do next.
