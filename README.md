# journal-review-simulator

A **local, Docker-deployable web platform** that simulates a scientific journal/conference
submission and peer-review workflow. It helps you **pre-evaluate a manuscript before real
submission** — it is a pre-submission editorial *simulator*, not real peer review.

> **Architecture principle:** Markdown/YAML is the semantic memory · the database is only an
> index + workflow state · the web app is the workflow · agents are independent evaluators ·
> Docker is reproducible deployment.

---

## 1. What it does

- Create a review with a unique ID (`REV-YYYYMMDD-HHMMSS-XXXXXX`) and a full documental tree.
- Upload a manuscript (PDF, DOCX, Markdown, LaTeX `.tex`, or ZIP with LaTeX) with safe validation.
- Extract the manuscript to Markdown (priority: LaTeX > Markdown > DOCX > PDF).
- Classify research area & paper type by keyword matching (never invents).
- Suggest / configure venues; import venue knowledge from Perplexity responses (Markdown/CSV).
- Generate external prompts for ChatGPT, Claude, Gemini, Perplexity and NotebookLM, and import their responses.
- Run an internal pipeline of independent reviewers + an integrity auditor + an editor-in-chief.
- Export a final review package (Markdown always; PDF best-effort) as a zip.

## 2. Architecture

| Layer | Tech | Notes |
|------|------|-------|
| Frontend | Next.js (App Router) + Tailwind | sidebar + 13-step review wizard |
| API | FastAPI | thin HTTP layer over the core library |
| Core | `worker/` Python package | single source of truth (imported by API **and** scripts) |
| DB | PostgreSQL (SQLite fallback locally) | index + workflow state only |
| Models | offline `template` engine by default | Claude / Ollama are pluggable seams |
| Deploy | Docker Compose | `web`, `api`, `worker`, `postgres`, optional `ollama` |

The documental memory lives under `data/` and is bind-mounted into the containers.

## 3. Run with Docker Compose

```bash
cp .env.example .env          # adjust if needed
docker compose up --build     # web → http://localhost:3000 , api → http://localhost:8000
# optional local models:
docker compose --profile ollama up --build
```

The API seeds the DB and indexes any venues already in `data/global_knowledge/venues/`.
To import the bundled Perplexity venue data on first run, see §7.

### Run without Docker (native, Windows-friendly)

```powershell
pip install -r apps/api/requirements.txt        # weasyprint is optional locally
$env:PYTHONPATH = "."
uvicorn app.main:app --app-dir apps/api --port 8000
# in apps/web:  npm install ; npm run dev
```

Without `DATABASE_URL` the API/scripts fall back to a local SQLite file at `data/jrs_local.db`.

## 4. Create a review

- **Web:** sidebar → *New Review* → set title + submission type → *Create*.
- **CLI:** `python scripts/init_review.py --title "My paper" --submission-type new_submission`

## 5. Upload a paper

In the review wizard, **Step 1 – Upload**, choose a file. Accepted: PDF, DOCX, MD, TeX, ZIP
(LaTeX), BibTeX, CSV, YAML, JSON. Uploads are validated for extension, real type, size, and safe
ZIP paths; a SHA256 and an `upload_report.md` are recorded.

- Markdown / PDF / DOCX: upload directly.
- LaTeX `.tex`: uploaded and read directly (best structure preservation).
- ZIP with LaTeX (+ figures + BibTeX): extracted in a sandbox; the main `.tex` is auto-detected.
- **Resubmission:** set the submission type accordingly and upload previous reviews / author
  response with the *kind* selector (`previous_review`, `author_response`).

CLI extraction: `python scripts/parse_paper.py --review-id <id> --file path/to/manuscript.tex`

## 6. Configure venues

- **Web:** sidebar → *Venues* → create manually, or import a CSV / Markdown table.
- Each venue is stored as documents under
  `data/global_knowledge/venues/journals/<venue_id>/` (`venue_profile.yaml` + Markdown docs).
- Unverified data is kept as `UNKNOWN` / `not verified` — the system never invents quartiles,
  rankings, impact factors or publication times.

## 7. Import the Perplexity venue database (now and later)

The Perplexity venue research arrives as Markdown tables or CSV. Two responses are bundled in
`docs/init_plan/perplexity_database_responses/`.

```bash
# copy the bundled responses into the import inbox, then import everything:
#   data/global_knowledge/venue_discovery/raw/
python scripts/import_venue_discovery.py                 # imports the whole raw/ folder
python scripts/import_venue_discovery.py --file my.csv   # import a single new response
```

The importer:
- auto-detects Markdown-table vs CSV (by content, not extension) and tolerates messy quoting/encoding;
- derives **stable slug IDs** from acronym/name (so the two batches' reused `V21/V22` IDs don't collide);
- writes per-venue docs, a normalized `processed/venues_normalized.{csv,json}`, and a dated report in
  `import_reports/`; and indexes everything in the DB.

Web: *Venues* → **Import venue discovery (Perplexity)** (upload) or **Re-import raw/ folder**.

> Future Perplexity responses: drop the file into `data/global_knowledge/venue_discovery/raw/`
> (or pass `--file`) and re-run — no overwrites thanks to stable IDs.

## 8. Add recent papers / SOTA

Place entries under `data/global_knowledge/recent_papers/<paper_id>/` (profile + summary +
relevance notes + citation). These feed the domain reviewer's novelty assessment (which stays
**provisional** until real literature is provided).

## 9. Generate external prompts

Review wizard **Step 7 – External Prompts** → *Generate prompts*. Prompts are created per
selected venue × reviewer × engine and saved under
`data/reviews/<id>/external_prompts/by_venue/<venue_id>/`. Each prompt states the exact expected
response filename:
`<review_id>__<venue_id>__rev{n}_<profile>_<engine>_response.md`.

## 10. Upload external responses

**Step 8 – External Responses** → upload the AI response (MD, PDF or DOCX). The system converts to
Markdown, validates the review ID, auto-detects engine/reviewer/venue from the filename, writes a
summary, and updates `external_responses/index.md`.

## 11. Manage pending requests

Reviewers may request more information (max **3** iterations per agent by default, configurable in
`config/pipeline.yaml`). Requests are stored under
`data/reviews/<id>/pending_requests/`. (Auto-raised requests activate with live reviewers.)

## 12. Run the internal pipeline

- **Web:** *Run full review* (top of the wizard), or run individual steps (Extraction, Venues,
  Autonomous Review, Integrity Audit, Editor Decision, Export).
- **CLI:**
  ```bash
  python scripts/run_pipeline.py --review-id <id> --mode full_review
  ```
  Supported modes: `init, validate_upload, extract, classify, scan_venues, discover_venues,
  venue_fit, timeline, desk_reject_precheck, literature_queries, generate_external_prompts,
  import_external_responses, review, specialized_review, integrity, editorial_decision, export,
  full_review`.

Reviewers (5 main + 6 specialized + 2 auditors) work **independently**. Outputs carry a metadata
block (review_id, venue_id, reviewer_profile, engine/model, sources, limitations, confidence).
By default they are deterministic Markdown scaffolds (offline `template` engine); swap in
Claude/Ollama in `worker/agent_orchestrator.py` / `config/model_config.yaml`.

## 13. Specialized reviewers

Auto-activated by detected areas: Document-AI/HTR, Education, Dataset/Benchmark,
Spectral/Agri/Food, FAS/Biometrics/Security, Cloud/HPC/Scheduling. Profiles live in
`data/global_knowledge/reviewer_profiles/` (canonical) and `.claude/agents/` (subagent defs).

## 14. Integrity audit

`integrity-ai-use-auditor` acts as an editorial checker (references, unsupported claims,
inconsistencies, undeclared AI use, data leakage, ethics, licenses, ...) →
`reviewer_outputs/integrity_ai_use_audit.md`. See the
`.claude/skills/review-paper-reviewer/SKILL.md` skill.

## 15. Editor decision & export

The editor reads the reviews + integrity audit + venue data and produces
`editor/{editor_decision,meta_review,revision_plan,rebuttal_strategy,final_letter}.md` — explaining
disagreements without mechanically averaging. Decisions: desk reject | reject | major revision |
minor revision | accept.

Export (**Step 13** or `python scripts/export_review_package.py --review-id <id>`) assembles
`exports/` and `full_review_package.zip`. PDF is best-effort (Markdown is always produced).

## 16. Compare Claude vs Ollama

`python scripts/compare_models.py --review-id <id> --provider ollama --model llama3.1`
writes comparison scaffolds to `reviewer_outputs/model_comparison/`.

## 16b. Run queries via engine CLI (Execute-query button)

Instead of manually copy-pasting prompts into LLM web UIs, the **External Prompts** step has an
**Execute query** control: pick a venue, reviewer and engine, and a worker runs that engine's
**local CLI** with the generated prompt and saves the output as an external response.

Supported engines (no API keys, no browser automation — they use the CLIs/plans you already have):

| Engine | CLI | Auth / cost |
|---|---|---|
| Claude | `claude -p` (Claude Code) | your Claude plan (e.g. Max) |
| ChatGPT | `codex exec` (OpenAI Codex CLI) | sign in with your ChatGPT plan (e.g. Pro) |
| Gemini | `gemini -p` (Gemini CLI) | free tier with a Google login |
| Ollama | `ollama run <model>` | local, free |

Command templates are in `config/model_config.yaml` (`cli_engines`) and are adjustable without code
changes. `GET /engine-status` reports which CLIs are installed. Perplexity is intentionally omitted.

### Host setup — run the CLIs from your own computer

Because the backend launches the CLI as a subprocess, **run the backend natively on your host**
(not in Docker — a container can't see host-installed CLIs or their cached logins).

**1) Install + authenticate each CLI (one time).** These use the plans you already have — no API
keys, no extra purchase:

| Engine | Install | Authenticate | Cost |
|---|---|---|---|
| Claude | comes with Claude Code | already signed in | your Claude plan (e.g. Max) |
| ChatGPT | `npm i -g @openai/codex` | run `codex`, *Sign in with ChatGPT* | your ChatGPT plan (e.g. Pro) |
| Gemini | `npm i -g @google/gemini-cli` | run `gemini`, log in with Google | **free tier** (no Pro needed) |
| Ollama | install Ollama, `ollama pull llama3.1` | n/a | local, free |

(npm needs Node.js — `winget install OpenJS.NodeJS.LTS`. The npm global bin
`%APPDATA%\npm` must be on PATH; open a new terminal after installing.)

**2) Start the backend natively** (SQLite fallback, no Docker/Postgres needed):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev_native.ps1
# prints which engine CLIs are detected, then serves the API on http://localhost:8000
```

**3) Use it — two ways:**

- **With the web UI:** in another terminal `cd apps\web; npm install; npm run dev` → open
  http://localhost:3000 → a review → step **7. External Prompts** → pick venue + reviewer + engine →
  **Execute query**. The engine dropdown disables CLIs that aren't installed.
- **Without any frontend** (quick check):
  ```powershell
  python scripts\run_query.py --status      # list detected engines
  python scripts\run_query.py --review-id <id> --venue <venue_id> --reviewer reviewer-methodology --engine codex
  ```

The response is saved as an indexed external response under
`data/reviews/<id>/external_responses/by_venue/<venue_id>/` and appears in the responses index.

> Note: queries consume each plan's **included** usage (Claude Max / ChatGPT Pro / Gemini free
> tier) — nothing extra to buy.

E2E tests for the UI live in `apps/web/e2e/` (Playwright) — see that folder's README.

## 17. View history

Sidebar → *Export / History* lists every review with download links; or browse `data/reviews/`.

## 18. What goes to GitHub

**Versioned:** code, templates, prompts, generic reviewer profiles, schemas, config examples,
documentation, and the venue knowledge base under `data/global_knowledge/`.

**Ignored by default** (`.gitignore`): `data/reviews/`, `data/uploads/`, PDFs, ZIPs, `.env`, API
keys, local models, temporary files. For large versioned files, document Git LFS (not auto-enabled).

## 19. Project layout

```
apps/web   Next.js frontend            apps/api   FastAPI backend
worker/    core library (shared)       config/    yaml configuration
db/        schema.sql + seed           scripts/   CLI entrypoints
data/global_knowledge/  venues, venue_discovery, reviewer_profiles, recent_papers, ...
data/reviews/<id>/      per-review documental tree
.claude/agents          18 subagents   .claude/skills  integrity skill
```

## 20. Verify the install

```bash
python scripts/check_structure.py                     # structure check
python scripts/import_venue_discovery.py              # import bundled venues
python scripts/init_review.py --title "Smoke test"    # -> prints a review id
python scripts/run_pipeline.py --review-id <id> --mode full_review
docker compose config                                 # validate compose
```

## Recommended next steps

1. Wire live Claude/Ollama reviewers in `worker/agent_orchestrator.py`.
2. Add an async task queue (arq/RQ) for long reviews.
3. Build the recent-papers upload UI and the pending-request loop.
4. Add the full Perplexity venue batch when it is ready (drop into `venue_discovery/raw/`).
5. Add PDF rendering assets if you need guaranteed PDF exports.
