# How to continue the session

_Standby 2026-06-07, resuming ~2026-06-09. master == origin/master @ `b03afad`._

## 30-second recap
Working MVP + heavy UI/UX hardening + a proven real-engine run. Hybrid system: deterministic parts are
real (extraction, classification, venue ranking, desk-reject); reviewers/integrity/editor are template
scaffolds by default but really run the agent CLI when `PIPELINE_ENGINE` is set (proven on PAPER_A with
claude). Read `STATE.md` first.

## Restart the servers (native — needed for engine CLIs)
`:3000` is OpenWebUI, so the web runs on **:3001**.

```powershell
# 1) API (template engine, SQLite, no Docker needed)
cd C:\Users\Usuari\Desktop\journal-review-simulator
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --app-dir apps\api --host 127.0.0.1 --port 8000
#   -> for REAL agents in the browser instead, prefix:  $env:PIPELINE_ENGINE="claude"  (or codex)

# 2) Web (new terminal)
cd C:\Users\Usuari\Desktop\journal-review-simulator\apps\web
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npx next dev -p 3001
#   open http://localhost:3001
```
If port 8000 is stuck from an old run: `Get-NetTCPConnection -LocalPort 8000 | %{ Stop-Process -Id $_.OwningProcess -Force }`.

Sanity: `$env:PYTHONPATH="."; python -m pytest tests/ -q` → 36 passed.

## First things on resume
1. `git status` (should be clean) + read `STATE.md` + this file.
2. Restart the two servers (above). Open `colapri` / PAPER_A in Edge to see the latest UI.
3. Decide the engine question below.

## The open question (where we paused)
The user asked: *"is it mocked or do we run real agents?"* — answer: hybrid (see STATE.md). The pending
decision: **do they want the web API to run with a real engine** so browser "Run" buttons produce real
agent content?
- **`codex` (ChatGPT Pro):** run `codex` once to log in, then start the API with `$env:PIPELINE_ENGINE="codex"`.
  Separate process → more reliable than nested claude. Recommended for real web runs.
- **`claude`:** works but nested-in-Claude-Code is flaky/slow (first call can hang ~5 min).
- **`ollama`:** install + `ollama pull llama3.1` for free local runs.
Caveat: a real full_review is ~9 CLI calls (minutes) and blocks the synchronous request; template stays instant.

## Candidate next steps
- **Wire desk-reject style real heuristics** to more steps, or make the precheck optionally engine-backed.
- **Async task queue** (arq/RQ) so real-engine runs don't block the web request (currently synchronous).
- **Per-step "Run" with real engine from the web** once an engine is wired into the API.
- Review PAPER_B/PAPER_C against their correct venues (Scientific Data / agri venues) with a real engine.
- Optional: merge the near-duplicate `dib`/`dib-2` venues; improve the venue Markdown-table importer to
  flag cell-count mismatches (the 6 repaired venues were a symptom).
- Clean up extra test/demo reviews under `data/reviews/` if desired (all gitignored).

## Gotchas / reminders
- Web on **:3001** (3000 = OpenWebUI). API on :8000. CORS allows any localhost port now.
- Don't `pip install weasyprint` natively on Windows (Docker-only).
- Bash tool working dir persists; `cd` to the repo root explicitly.
- `data/reviews/`, `data/uploads/`, `*.db`, and `apps/web/e2e/papers/*` (your PDFs) are gitignored.
- Frequent API restarts cause a brief "Failed to fetch" in the web — now silenced in the poll.
- Charset: the product is UTF-8 clean; `curl | python` on Windows mis-renders accents in diagnostics only.

## Ready-to-paste kickoff prompt
> Continue the `journal-review-simulator`. Read docs/session_log/STATE.md, bitacora.md and CONTINUE.md to
> recover context (we are on master @ the latest commit; servers are stopped — restart per CONTINUE.md).
> Then [pick: e.g. "start the web API with PIPELINE_ENGINE=codex (after I log in to codex) so the browser
> Run buttons produce real agent reviews", or "add an async queue so real-engine runs don't block"].
> Keep the approved deviations (DECISIONS.md) and the hybrid template/real-engine design.
