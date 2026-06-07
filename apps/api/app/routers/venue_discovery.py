"""Venue-discovery importer endpoints (the emphasized feature).

Import a Perplexity response (Markdown pipe-table or CSV) by upload, by raw
text, or from a file already dropped in
``data/global_knowledge/venue_discovery/raw/``.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from worker import venue_discovery as vd
from worker.paths import global_knowledge_dir

router = APIRouter(prefix="/venue-discovery", tags=["venue-discovery"])


class ImportTextIn(BaseModel):
    text: str
    source_name: str = "pasted_response.md"


def _result_dict(r: vd.ImportResult) -> dict:
    return {
        "source": r.source,
        "detected_format": r.detected_format,
        "imported": len(r.venues),
        "skipped": r.skipped,
        "collisions_resolved": r.collisions_resolved,
        "report_path": r.report_path,
        "processed_json": r.processed_json,
        "processed_csv": r.processed_csv,
        "venues": [{"venue_id": v.venue_id, "source_ref": v.source_ref,
                    "name": v.raw.get("name", "")} for v in r.venues],
    }


@router.post("/import")
async def import_upload(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    result = vd.import_bytes(data, source_name=file.filename or "upload", index_in_db=True)
    return _result_dict(result)


@router.post("/import-text")
def import_text(body: ImportTextIn) -> dict:
    result = vd.import_text(body.text, source_name=body.source_name, index_in_db=True)
    return _result_dict(result)


@router.post("/import-raw-dir")
def import_raw_dir() -> dict:
    results = vd.import_raw_dir(index_in_db=True)
    return {
        "files_processed": len(results),
        "results": [_result_dict(r) for r in results],
    }


@router.get("/reports")
def list_reports() -> dict:
    rep_dir = global_knowledge_dir() / "venue_discovery" / "import_reports"
    if not rep_dir.exists():
        return {"reports": []}
    reports = sorted((p.name for p in rep_dir.glob("*.md")), reverse=True)
    return {"reports": reports}


@router.get("/reports/{name}")
def get_report(name: str) -> dict:
    rep_dir = global_knowledge_dir() / "venue_discovery" / "import_reports"
    target = (rep_dir / name).resolve()
    if not str(target).startswith(str(rep_dir.resolve())) or not target.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return {"name": name, "content": target.read_text(encoding="utf-8")}
