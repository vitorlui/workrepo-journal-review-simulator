"""High-level review lifecycle helpers (create / list / get).

Keeps the API and CLI thin. A review is created on disk (the documental tree)
and indexed in the DB.
"""
from __future__ import annotations

from dataclasses import dataclass

from worker.markdown_store import read_yaml
from worker.paths import review_dir, reviews_dir
from worker.review_id import create_review_tree, new_review_id


@dataclass
class ReviewInfo:
    review_id: str
    title: str
    status: str
    submission_type: str
    current_step: int
    paper_type: str
    detected_areas: list
    final_decision: str | None
    path_on_disk: str


def create_review(title: str = "UNKNOWN", submission_type: str = "new_submission") -> ReviewInfo:
    review_id = new_review_id()
    root = create_review_tree(review_id, title=title, submission_type=submission_type)

    try:
        from worker.db import Review, session_scope
        with session_scope() as s:
            s.add(Review(
                review_id=review_id, title=title, submission_type=submission_type,
                status="created", current_step=0, path_on_disk=str(root),
            ))
    except Exception:
        pass

    return ReviewInfo(
        review_id=review_id, title=title, status="created", submission_type=submission_type,
        current_step=0, paper_type="UNKNOWN", detected_areas=[], final_decision=None,
        path_on_disk=str(root),
    )


def _info_from_meta(review_id: str) -> ReviewInfo | None:
    meta = read_yaml(review_dir(review_id) / "metadata.yaml")
    if not meta:
        return None
    return ReviewInfo(
        review_id=meta.get("review_id", review_id),
        title=meta.get("title", "UNKNOWN"),
        status=meta.get("status", "created"),
        submission_type=meta.get("submission_type", "new_submission"),
        current_step=meta.get("current_step", 0),
        paper_type=meta.get("paper_type", "UNKNOWN"),
        detected_areas=meta.get("detected_area_labels") or meta.get("detected_areas", []),
        final_decision=meta.get("final_decision"),
        path_on_disk=str(review_dir(review_id)),
    )


def get_review(review_id: str) -> ReviewInfo | None:
    return _info_from_meta(review_id)


def list_reviews() -> list[ReviewInfo]:
    base = reviews_dir()
    if not base.exists():
        return []
    out = []
    for d in sorted(base.iterdir(), reverse=True):
        if d.is_dir() and (d / "metadata.yaml").exists():
            info = _info_from_meta(d.name)
            if info:
                out.append(info)
    return out


def set_selected_venues(review_id: str, venue_ids: list[str]) -> None:
    from worker.markdown_store import write_yaml
    path = review_dir(review_id) / "metadata.yaml"
    meta = read_yaml(path)
    meta["selected_venues"] = venue_ids
    write_yaml(path, meta)
    try:
        from sqlalchemy import select
        from worker.db import Review, session_scope
        with session_scope() as s:
            r = s.scalar(select(Review).where(Review.review_id == review_id))
            if r is not None and venue_ids:
                r.selected_venue_id = venue_ids[0]
    except Exception:
        pass
