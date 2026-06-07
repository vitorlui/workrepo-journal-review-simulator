# Current state snapshot

_As of 2026-06-07 (standby; resuming ~2026-06-09). master == origin/master @ `b03afad`._

## TL;DR
Working MVP + a lot of UI/UX hardening and a proven real-engine run. The product is a **hybrid**:
deterministic parts are real; the reviewer/integrity/editor agents are template scaffolds by default
but really execute the engine CLI when configured. 36 pytest pass. Everything committed + pushed.

## What is REAL vs TEMPLATE (important — the user asked)
- **REAL / deterministic:** manuscript extraction (pypdf/python-docx/LaTeX), area classification
  (whole-token keyword match), venue discovery + ranking (family overlap), **desk-reject precheck**
  (heuristics from the extraction), safe upload (hash/MIME/ZIP sandbox), venue import.
- **TEMPLATE by default, REAL with an engine:** the 4 main reviewers + specialized + integrity audit +
  editor. With `PIPELINE_ENGINE=template` (default) → Markdown scaffolds showing "pending". With
  `PIPELINE_ENGINE=claude|codex|ollama|gemini` → they really run the CLI agent (proven: PAPER_A reviewed
  by real claude → MAJOR REVISION vs DESK REJECT by venue).
- **The web API runs `template` by default**, so browser "Run" buttons produce scaffolds. To get real
  agents in the browser, start the API with `PIPELINE_ENGINE` set (see CONTINUE.md).

## Environment
- Windows 11. Python 3.13. Node **v24** (winget). CLIs installed: `claude` (Claude Code), `codex`
  (`%APPDATA%\npm`, needs `codex` login once), `gemini` (needs Google login once). `ollama` not installed.
- Extra Python deps installed this session: `ftfy`, `pytest`, `fastapi`, `httpx`, plus the API runtime deps.
- **Ports:** `:3000` is the user's **OpenWebUI** — our **web runs on :3001**, API on **:8000**.
- Docker images built earlier (web/api/worker). Native run is what's used for engine CLIs.

## Servers (were running this session; restart on resume — see CONTINUE.md)
- API (uvicorn) on `127.0.0.1:8000`, engine = `template`.
- Web (`next dev -p 3001`) on `localhost:3001`, `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Reviews on disk (data/reviews/, gitignored)
- **PAPER_A** `REV-20260607-170748-B984L5` (wheat/DON NIR-HSI) — full real-claude review vs **Scientific
  Data** → **MAJOR REVISION** (6/7 reviewers real). Cleaned areas: agri-food, ML/CV, dataset.
- **PAPER_B** `REV-...-7FL9FX`, **PAPER_C** `REV-...-5GUZDT` — completed with template engine.
- **colapri** `REV-20260607-190503-3GJFH2` — a **cloud** paper, full template review; desk-reject now
  shows 4 real gap flags.
- (A couple of E2E/test reviews may also exist; all gitignored.)

## Key files added/changed this session
- Backend: `worker/summary.py` (results digest), `worker/engines/cli_engine.py` (UTF-8 + ftfy + temp-file
  stdin), `worker/classify.py` (whole-token), `worker/venues.py` (ranking + real desk-reject),
  `worker/pipeline_runner.py` (per-step status, completed status, decision parse, title auto-id),
  `apps/api/app/routers/reviews.py` (`/summary`, `/venue-candidates`).
- Frontend: `apps/web/app/reviews/[id]/page.tsx` (running panel, ETA, notifications, auto-refresh tick,
  dimmed steps + Next button, Results view, venue ranking, pending placeholders, robust artifact panel),
  `components/Markdown.tsx`, `components/HelpButton.tsx` (guided tour).
- E2E: `apps/web/e2e/{smoke,review-flow,help,paper-runs}.spec.ts`, `papers/` (PAPER_A/B/C, gitignored).

## Tests
`$env:PYTHONPATH="."; python -m pytest tests/ -q` → **36 passed**.

## Known limitations / next (see CONTINUE.md)
- Web API on template → browser runs are scaffolds unless engine set.
- Nested `claude -p` inside Claude Code is flaky/slow (first call can hang to timeout). `codex`/`ollama`
  (separate processes) are more reliable for real runs.
- An orphan uvicorn from a `&`-launched restart may linger; kill by port 8000 on resume if needed.
