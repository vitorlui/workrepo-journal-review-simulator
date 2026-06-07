"""Reviews: create/list/get, uploads, extraction view, venue selection, artifacts."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from worker import reviews as review_svc
from worker.file_ingestion import ingest_file
from worker.markdown_store import read_yaml
from worker.paths import review_dir

router = APIRouter(prefix="/reviews", tags=["reviews"])


class CreateReviewIn(BaseModel):
    title: str = "UNKNOWN"
    submission_type: str = "new_submission"


class SelectVenuesIn(BaseModel):
    venue_ids: list[str]


def _info_dict(info) -> dict:
    return {
        "review_id": info.review_id,
        "title": info.title,
        "status": info.status,
        "submission_type": info.submission_type,
        "current_step": info.current_step,
        "paper_type": info.paper_type,
        "detected_areas": info.detected_areas,
        "final_decision": info.final_decision,
        "path_on_disk": info.path_on_disk,
    }


@router.post("")
def create_review(body: CreateReviewIn) -> dict:
    info = review_svc.create_review(title=body.title, submission_type=body.submission_type)
    return _info_dict(info)


@router.get("")
def list_reviews() -> list[dict]:
    return [_info_dict(i) for i in review_svc.list_reviews()]


@router.get("/{review_id}")
def get_review(review_id: str) -> dict:
    info = review_svc.get_review(review_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Review not found")
    meta = read_yaml(review_dir(review_id) / "metadata.yaml")
    data = _info_dict(info)
    data["metadata"] = meta
    return data


@router.post("/{review_id}/uploads")
async def upload_file(
    review_id: str,
    file: UploadFile = File(...),
    kind: str = Form("manuscript"),
) -> dict:
    if review_svc.get_review(review_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    data = await file.read()
    result = ingest_file(review_id, original_filename=file.filename or "upload", data=data, kind=kind)
    if result.ok:
        try:
            from sqlalchemy import select
            from worker.db import UploadedFile, session_scope
            with session_scope() as s:
                s.add(UploadedFile(
                    review_id=review_id, original_filename=result.original_filename,
                    stored_filename=Path(result.stored_path).name if result.stored_path else "",
                    extension=result.extension, mime_type=result.mime_type,
                    size_bytes=result.size_bytes, sha256=result.sha256, kind=result.kind,
                    path_on_disk=str(result.stored_path) if result.stored_path else "",
                ))
        except Exception:
            pass
    return result.to_dict()


@router.get("/{review_id}/extracted")
def get_extraction(review_id: str) -> dict:
    root = review_dir(review_id) / "extracted"
    md = root / "paper_extraction.md"
    js = root / "paper_extraction.json"
    if not md.exists():
        raise HTTPException(status_code=404, detail="No extraction yet. Run extract first.")
    import json
    return {
        "markdown": md.read_text(encoding="utf-8"),
        "fields": json.loads(js.read_text(encoding="utf-8")).get("fields", {}) if js.exists() else {},
    }


@router.post("/{review_id}/select-venues")
def select_venues(review_id: str, body: SelectVenuesIn) -> dict:
    if review_svc.get_review(review_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    review_svc.set_selected_venues(review_id, body.venue_ids)
    return {"review_id": review_id, "selected_venues": body.venue_ids}


@router.get("/{review_id}/artifact")
def get_artifact(review_id: str, relpath: str) -> dict:
    """Return the text content of a file inside the review tree (path-safe)."""
    root = review_dir(review_id).resolve()
    target = (root / relpath).resolve()
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=400, detail="Path traversal blocked")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    try:
        return {"relpath": relpath, "content": target.read_text(encoding="utf-8")}
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Artifact is not text")


@router.get("/{review_id}/tree")
def list_artifacts(review_id: str) -> dict:
    """List markdown/json/yaml artifacts in the review tree for the UI."""
    root = review_dir(review_id)
    if not root.exists():
        raise HTTPException(status_code=404, detail="Review not found")
    files = []
    for ext in ("*.md", "*.json", "*.yaml", "*.csv"):
        for p in root.rglob(ext):
            files.append(str(p.relative_to(root)).replace("\\", "/"))
    return {"review_id": review_id, "files": sorted(files)}
