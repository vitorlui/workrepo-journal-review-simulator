# How to continue the session

## 30-second recap
We built a working MVP of `journal-review-simulator` (Next.js + FastAPI + `worker/` core +
Postgres/SQLite). 37 venues imported from the bundled Perplexity files. Offline `template`
pipeline runs end to end. Added **CLI engine integration**: the "Execute query" button runs
`claude`/`codex`/`gemini`/`ollama` with our generated prompt and saves the response. 32 pytest
pass; Docker images build. Work is on branch `feat/mvp-scaffold`.

## First things to do when resuming
1. `git status` and read `docs/session_log/STATE.md` (current state) + `bitacora.md` (history).
2. If not merged yet: `git checkout master && git merge --ff-only feat/mvp-scaffold`.
3. Sanity: `cd <repo>; $env:PYTHONPATH="."; python -m pytest tests/ -q` → expect 32 passed.
4. To try the engine CLIs live: `python scripts\run_query.py --status` (codex/gemini need a
   one-time login: run `codex` / `gemini` once and sign in).

## Candidate next steps (not yet done)
- ~~Wire engines into the internal pipeline~~ **DONE** (2026-06-07): `agent_orchestrator` runs the
  real CLI for reviewers/integrity/editor when `PIPELINE_ENGINE` is set, with offline fallback.
  Next polish: per-call model-comparison output, or per-venue parallelism.
- **End-to-end real-engine run:** set `PIPELINE_ENGINE=codex` (or claude/gemini, logged in),
  `python scripts/run_pipeline.py --review-id <id> --mode full_review`, and review the generated
  Markdown for quality. (Slow: ~10 CLI calls.)
- **Run the Playwright E2E** now that Node is installed: `cd apps/web; npm install;
  npm run test:e2e:install; npm run test:e2e` (stack must be up).
- **"Review my pending papers"** flow: the user offered to provide real papers; ingest them
  into reviews and generate real reviews (Claude/Codex) directly.
- **Per-prompt Execute-query buttons** (currently one combined control in step 7) + a
  "run all reviewers for engine X" batch action.
- **Import the full Perplexity venue batch** when ready: drop into
  `data/global_knowledge/venue_discovery/raw/` and `python scripts/import_venue_discovery.py`.
- **Pending-requests loop** + **recent-papers upload UI** (currently stubs).
- Optional: provision the CLIs inside a worker image, or add an async queue.

## Ready-to-paste kickoff prompt for the next session
> Continue the `journal-review-simulator` project. Read `docs/session_log/STATE.md`,
> `bitacora.md`, and `DECISIONS.md` first to recover context. We are on branch
> `feat/mvp-scaffold` (merge to master if not done). Then [pick a next step from
> `CONTINUE.md`, e.g. "wire the engine CLIs into the internal reviewer pipeline with offline
> fallback and add a test"]. Keep the approved A/B/C deviations and the CLI-over-API stance.

## Gotchas / reminders
- Windows shell: don't `pip install weasyprint` natively (GTK pain) — it's Docker-only.
- The Bash tool's working directory persists between calls; `cd` to the repo root explicitly.
- Engine CLIs only work when the backend runs **natively** (not in Docker).
- `data/reviews/`, `data/uploads/`, `*.db` are gitignored; `data/global_knowledge/**` is versioned.
- Don't re-run the importer against already-imported venues without clearing
  `venues/journals/` first, or you get `-2` suffixed duplicates.
