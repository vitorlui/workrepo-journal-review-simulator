# Current state snapshot

_As of 2026-06-07. Update at end of each session._

## TL;DR
A working MVP of the pre-submission editorial review simulator: Next.js UI + FastAPI +
shared `worker/` core + Postgres/SQLite index. **37 venues imported.** Offline `template`
pipeline runs end to end. **CLI engine integration** lets a worker run `claude`/`codex`/
`gemini`/`ollama` with the generated prompt ("Execute query" button). 32 pytest pass;
Docker images build.

## Environment
- OS: Windows 11. Shell: PowerShell (+ bash available).
- Python: **3.13** (Windows Store). Key deps installed: sqlalchemy, pyyaml, fastapi,
  python-multipart, httpx, pytest. (Native run also needs uvicorn/pypdf/python-docx/filetype —
  `dev_native.ps1` installs them. **weasyprint is Docker-only**; do NOT `pip install` it on Windows.)
- Node: **v24.16.0** (installed via winget this session). npm v11.
- CLIs installed on host: **codex**, **gemini** at `%APPDATA%\npm\` (need one-time login).
  `claude` available via Claude Code. `ollama` not installed.
- Docker Desktop: running; images built (web 1.01 GB, api/worker 459 MB).

## Architecture (see README §2 + DECISIONS.md)
- **`worker/` = single core library** (C6): imported by `apps/api` and `scripts/`.
- **API** = thin FastAPI over `worker/`; runs pipeline **in-process** (no queue) for MVP.
- **DB** = index/workflow-state only; ORM models canonical, `db/schema.sql` generated (C9).
  Postgres in Docker, **SQLite fallback** locally (`data/jrs_local.db`, gitignored).
- **Markdown/YAML under `data/` is the semantic memory** (bind-mounted in Docker).

## File map (key)
```
worker/         review_id, file_ingestion, extraction, classify, markdown_store,
                external_prompt_manager, agent_orchestrator, pipeline_runner, exporters,
                venues, venue_discovery, reviews, external_responses, db, paths, run_query,
                engines/ (base, cli_engine, ollama_engine, openai_engine, __init__)
apps/api/app/   main.py, core.py, routers/{reviews,pipeline,venues,venue_discovery,
                responses,catalog,export}.py
apps/web/       app/ (layout + page + reviews/[id] wizard + venues + reviewer-profiles +
                ai-engines + papers + ... ), components/Sidebar, lib/api.ts, e2e/ (Playwright)
config/         pipeline, scoring_rubrics, model_config (+cli_engines), reviewer_profiles,
                venue_discovery, external_engines, upload_policy .yaml
db/             schema.sql (generated), seed/*.sql
scripts/        run_pipeline, init_review, parse_paper, discover_venues, scan_venue_markdowns,
                import_venue_discovery, build_literature_matrix, compare_models, build_report,
                export_review_package, check_structure, dump_schema, run_query, dev_native.ps1
data/global_knowledge/  venues/journals/<37 venues>, venue_discovery/{raw,processed,import_reports},
                reviewer_profiles/<13>, venues/template, recent_papers, ...
.claude/        agents/<18>, skills/review-paper-reviewer/SKILL.md
tests/          conftest, test_worker_core, test_venue_discovery, test_pipeline, test_api, test_engines
```

## Verified working
- `python scripts/check_structure.py` → 57/57.
- Venue importer on both bundled files → 37 venues, processed CSV/JSON + import report,
  unverified values preserved, UTF-8 correct.
- Full pipeline (`--mode full_review`) → extraction, classification (FAS/HTR/cloud detected on
  the sample), candidate venues, external prompts, 5 main + specialized reviewers, integrity
  audit, editor decision package, export zip, audit log.
- FastAPI via TestClient (health, dashboard, venues=37, reviewer-profiles 5/6/2, pipeline,
  engine-status, run-query route).
- CLI engine: `claude -p` executed live from the worker; unavailable CLIs degrade gracefully.
- **`pytest tests/` → 32 passed.**

## Git
- Branch **`feat/mvp-scaffold`**. Commits: `32342f4` (initial, pre-session) →
  `a7ab4d9` (MVP) → `fde22d3` (CLI integration + E2E) → (pending: launcher/docs/logbook).
- `master` still at `32342f4` — **merge pending** (recommended).
- No git remote configured (local only).

## How to run
- **Full stack (Docker):** `docker compose up --build` → web :3000, api :8000.
- **Native (to use host CLIs):** `powershell -ExecutionPolicy Bypass -File scripts\dev_native.ps1`
  (API :8000, SQLite) + `cd apps\web; npm install; npm run dev` (web :3000).
- **Import venues:** `python scripts/import_venue_discovery.py`.
- **Run a CLI query w/o frontend:** `python scripts/run_query.py --status` then
  `--review-id <id> --venue <vid> --reviewer reviewer-methodology --engine codex`.

## Known limitations / not done (by design for MVP)
- Internal reviewers are **offline template scaffolds** unless `PIPELINE_ENGINE`/Execute-query
  uses a real CLI. (Seam in `worker/agent_orchestrator.py` not yet wired to engines for the
  internal pipeline — only the Execute-query button uses engines so far.)
- No async task queue (in-process).
- PDF export best-effort (weasyprint only in Docker image).
- Perplexity engine intentionally omitted.
- Recent-papers upload UI and pending-request auto-loop are stubs.
- Playwright specs written but not executed here (Node was just installed; run them now).
