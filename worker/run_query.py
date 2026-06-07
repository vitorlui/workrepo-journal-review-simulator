"""Execute-query orchestration.

Builds the reviewer prompt, runs it through an engine CLI, and saves the output
as an indexed external response. Backs the "Execute query" button.
"""
from __future__ import annotations

from worker.engines import run_query
from worker.external_prompt_manager import build_execution_prompt
from worker.external_responses import save_generated_response


def execute_query(review_id: str, venue_id: str, reviewer_profile: str, engine: str) -> dict:
    prompt = build_execution_prompt(review_id, venue_id, reviewer_profile, engine)
    result = run_query(engine, prompt)
    saved = save_generated_response(
        review_id, venue_id=venue_id, reviewer_profile=reviewer_profile, engine=engine,
        content=result.text, model=result.model, error=result.error or "",
    )
    return {
        "ok": result.ok,
        "engine": engine,
        "model": result.model,
        "error": result.error,
        "stored_path": saved.stored_path,
        "looks_incomplete": saved.looks_incomplete,
        "preview": (result.text or "")[:1500],
    }
