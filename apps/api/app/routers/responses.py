"""External prompts index, external response import, and pending requests."""
from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from worker import reviews as review_svc
from worker.external_responses import import_response
from worker.paths import review_dir
from worker.run_query import execute_query

router = APIRouter(prefix="/reviews", tags=["external"])


class RunQueryIn(BaseModel):
    venue_id: str
    reviewer_profile: str
    engine: str  # claude | codex | ollama | gemini


@router.get("/{review_id}/external-prompts")
def external_prompts(review_id: str) -> dict:
    index = review_dir(review_id) / "external_prompts" / "index.md"
    if not index.exists():
        return {"index": "", "exists": False}
    return {"index": index.read_text(encoding="utf-8"), "exists": True}


@router.post("/{review_id}/external-responses")
async def upload_response(review_id: str, file: UploadFile = File(...)) -> dict:
    if review_svc.get_review(review_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    data = await file.read()
    res = import_response(review_id, filename=file.filename or "response.md", data=data)
    return {
        "venue_id": res.venue_id,
        "reviewer_profile": res.reviewer_profile,
        "engine": res.engine,
        "stored_path": res.stored_path,
        "has_sources": res.has_sources,
        "looks_incomplete": res.looks_incomplete,
        "warnings": res.warnings,
    }


@router.post("/{review_id}/run-query")
def run_query(review_id: str, body: RunQueryIn) -> dict:
    """Run the generated prompt through an engine CLI and save the response."""
    if review_svc.get_review(review_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return execute_query(review_id, body.venue_id, body.reviewer_profile, body.engine)


@router.get("/{review_id}/external-responses")
def list_responses(review_id: str) -> dict:
    index = review_dir(review_id) / "external_responses" / "index.md"
    return {"index": index.read_text(encoding="utf-8") if index.exists() else "", "exists": index.exists()}


@router.get("/{review_id}/pending-requests")
def pending_requests(review_id: str) -> dict:
    js = review_dir(review_id) / "pending_requests" / "pending_requests.json"
    if not js.exists():
        return {"pending_requests": []}
    try:
        return {"pending_requests": json.loads(js.read_text(encoding="utf-8"))}
    except Exception:
        return {"pending_requests": []}
