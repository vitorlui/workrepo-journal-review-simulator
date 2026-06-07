"""Static catalogs: reviewer profiles, AI engines, dashboard counters."""
from __future__ import annotations

from fastapi import APIRouter

from worker import reviews as review_svc
from worker import venues as venue_mod
from worker.markdown_store import read_text
from worker.paths import REPO_ROOT, load_config

router = APIRouter(tags=["catalog"])


@router.get("/reviewer-profiles")
def reviewer_profiles() -> dict:
    cfg = load_config("reviewer_profiles")
    out = {"main_reviewers": [], "specialized_reviewers": [], "auditors": []}
    for group in out:
        for p in cfg.get(group, []):
            md = REPO_ROOT / p.get("profile_md", "")
            out[group].append({
                "id": p["id"],
                "title": p.get("title", ""),
                "activation_areas": p.get("activation_areas", []),
                "default_enabled": p.get("default_enabled", group != "specialized_reviewers"),
                "has_profile_md": md.exists(),
                "summary": (read_text(md).splitlines()[0] if md.exists() else "NEEDS_USER_INPUT"),
            })
    return out


@router.get("/ai-engines")
def ai_engines() -> dict:
    ext = load_config("external_engines")
    model = load_config("model_config")
    return {
        "external_engines": ext.get("engines", []),
        "internal_modes": ext.get("internal_modes", []),
        "internal_engines": model.get("engines", {}),
        "default_engine": model.get("default_engine", "template"),
    }


@router.get("/engine-status")
def engine_status() -> dict:
    """Which CLI engines are installed/available for the Execute-query button."""
    from worker.engines import engine_status as status
    from worker.engines import query_engines
    return {"engines": status(), "query_engines": query_engines()}


@router.get("/dashboard")
def dashboard() -> dict:
    reviews = review_svc.list_reviews()
    venues = venue_mod.list_venues()
    by_status: dict[str, int] = {}
    for r in reviews:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    return {
        "reviews_total": len(reviews),
        "reviews_by_status": by_status,
        "venues_total": len(venues),
        "recent_reviews": [
            {"review_id": r.review_id, "title": r.title, "status": r.status,
             "submission_type": r.submission_type, "paper_type": r.paper_type}
            for r in reviews[:8]
        ],
    }
