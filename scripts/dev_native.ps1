# Run the backend NATIVELY on your Windows host so it can reach the engine CLIs
# (claude / codex / gemini / ollama). Docker cannot see host-installed CLIs.
#
#   powershell -ExecutionPolicy Bypass -File scripts\dev_native.ps1
#
# Uses the local SQLite fallback (no Postgres/Docker needed). API -> http://localhost:8000

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

# Make Node-based CLIs (codex, gemini) discoverable in this session.
$nodeDir = "C:\Program Files\nodejs"
$npmBin  = Join-Path $env:APPDATA "npm"
$env:Path = "$nodeDir;$npmBin;$env:Path"

# Core Python deps for a native run (no weasyprint: PDF stays best-effort; no psycopg: SQLite).
Write-Host "Ensuring core Python dependencies..." -ForegroundColor Cyan
python -m pip install --quiet --disable-pip-version-check `
  fastapi "uvicorn[standard]" python-multipart SQLAlchemy PyYAML pypdf python-docx filetype | Out-Null

# Environment: SQLite fallback, host data dir.
$env:PYTHONPATH = "$repo;$repo\apps\api"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$env:PIPELINE_ENGINE = "template"

Write-Host "`nEngine CLI availability:" -ForegroundColor Cyan
python -c "from worker.engines import engine_status; import json; print(json.dumps({k:{'available':v['available'],'resolved':v['resolved']} for k,v in engine_status().items()}, indent=2))"

Write-Host "`nStarting API on http://localhost:8000  (Ctrl+C to stop)" -ForegroundColor Green
python -m uvicorn app.main:app --app-dir "$repo\apps\api" --host 0.0.0.0 --port 8000 --reload
