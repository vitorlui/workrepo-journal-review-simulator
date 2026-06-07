"""Review ID generation and the per-review documental tree.

Review ID format (spec): ``REV-YYYYMMDD-HHMMSS-XXXXXX``.
"""
from __future__ import annotations

import random
import string
from datetime import datetime
from pathlib import Path

from worker.markdown_store import now_iso, write_yaml
from worker.paths import review_dir

_ALPHABET = string.ascii_uppercase + string.digits

# Subfolders created under data/reviews/<review_id>/ (spec layout).
_REVIEW_SUBDIRS = [
    "input/original",
    "input/previous_reviews",
    "input/author_response",
    "input/latex_source",
    "extracted",
    "venues/venue_snapshots",
    "literature/notes",
    "external_prompts/by_venue",
    "external_responses/by_venue",
    "pending_requests",
    "reviewer_outputs/internal",
    "reviewer_outputs/specialized",
    "reviewer_outputs/external_summaries",
    "reviewer_outputs/model_comparison",
    "editor",
    "exports",
    "audit",
]


def new_review_id(now: datetime | None = None) -> str:
    now = now or datetime.now()
    suffix = "".join(random.choices(_ALPHABET, k=6))
    return f"REV-{now:%Y%m%d}-{now:%H%M%S}-{suffix}"


def create_review_tree(
    review_id: str,
    *,
    title: str = "UNKNOWN",
    submission_type: str = "new_submission",
) -> Path:
    """Create the full folder tree + ``metadata.yaml`` for a review."""
    root = review_dir(review_id)
    for sub in _REVIEW_SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)

    metadata = {
        "review_id": review_id,
        "title": title,
        "submission_type": submission_type,
        "status": "created",
        "current_step": 0,
        "paper_type": "UNKNOWN",
        "detected_areas": [],
        "selected_venues": [],
        "final_decision": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    write_yaml(root / "metadata.yaml", metadata)

    # Initialise audit artefacts.
    (root / "audit" / "audit_log.md").write_text(
        f"# Audit log — {review_id}\n\n- {now_iso()} — review created\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "audit" / "file_hashes.json").write_text("{}\n", encoding="utf-8", newline="\n")
    (root / "audit" / "model_usage.md").write_text(
        f"# Model usage — {review_id}\n\n"
        "| timestamp | agent | engine | model | mode |\n"
        "| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "audit" / "limitations.md").write_text(
        f"# Limitations — {review_id}\n\n"
        "This is a simulated pre-submission editorial review, not real peer review.\n",
        encoding="utf-8",
        newline="\n",
    )
    return root
