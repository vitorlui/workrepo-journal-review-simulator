"""End-to-end pipeline test (offline template engine)."""
from __future__ import annotations

from worker.file_ingestion import ingest_file
from worker.pipeline_runner import run_pipeline
from worker.paths import review_dir
from worker.reviews import create_review
from worker import venue_discovery as vd
from conftest import SAMPLE_PAPER, VENUE_FILE_1


def _seed_venues_once():
    if not list((vd.venues_dir() / "journals").glob("*/venue_profile.yaml")):
        vd.import_bytes(VENUE_FILE_1.read_bytes(), source_name="f1.csv", index_in_db=True)


def test_full_review_pipeline_produces_outputs():
    _seed_venues_once()
    info = create_review(title="pipeline e2e", submission_type="new_submission")
    rid = info.review_id
    ingest_file(rid, original_filename="manuscript.md", data=SAMPLE_PAPER.read_bytes(), kind="manuscript")

    result = run_pipeline(rid, "full_review")
    assert "extract" in result.steps
    assert "editorial_decision" in result.steps

    root = review_dir(rid)
    for rel in (
        "extracted/manuscript_extracted.md",
        "extracted/paper_extraction.json",
        "extracted/classification.md",
        "venues/candidate_venues.md",
        "external_prompts/index.md",
        "reviewer_outputs/integrity_ai_use_audit.md",
        "editor/editor_decision.md",
        "editor/revision_plan.md",
        "exports/full_review_package.zip",
        "audit/audit_log.md",
    ):
        assert (root / rel).exists(), f"missing {rel}"

    # Main reviewers ran for the auto-selected venue.
    internal = list((root / "reviewer_outputs" / "internal").glob("*.md"))
    assert len(internal) >= 5

    # Editor decision carries the mandatory metadata + no mechanical average note.
    decision = (root / "editor" / "editor_decision.md").read_text(encoding="utf-8")
    assert "do not mechanically average" in decision.lower()
    assert "confidence: NOT_VERIFIED" in decision


def test_classification_detects_fas_for_sample():
    info = create_review(title="classify e2e")
    rid = info.review_id
    ingest_file(rid, original_filename="manuscript.md", data=SAMPLE_PAPER.read_bytes(), kind="manuscript")
    run_pipeline(rid, "extract")
    run_pipeline(rid, "classify")
    import yaml
    meta = yaml.safe_load((review_dir(rid) / "metadata.yaml").read_text(encoding="utf-8"))
    assert "fas_biometrics_security" in meta["detected_areas"]


def test_unknown_mode_raises():
    info = create_review(title="bad mode")
    try:
        run_pipeline(info.review_id, "not_a_mode")
        assert False, "should have raised"
    except ValueError:
        pass
