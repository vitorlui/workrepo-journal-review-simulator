"""Run pipeline modes for a review."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from worker import reviews as review_svc
from worker.pipeline_runner import MODES, run_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/modes")
def list_modes() -> dict:
    return {"modes": MODES}


@router.post("/{review_id}/run")
def run(review_id: str, mode: str = "full_review") -> dict:
    if review_svc.get_review(review_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    if mode not in MODES:
        raise HTTPException(status_code=400, detail=f"Unknown mode '{mode}'")
    result = run_pipeline(review_id, mode)
    return result.to_dict()
