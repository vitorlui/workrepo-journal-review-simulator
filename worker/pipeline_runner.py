"""Pipeline orchestration.

``run_pipeline(review_id, mode)`` dispatches to a handler per spec mode, reads
and writes the Markdown semantic memory, updates the DB workflow state and
appends to the per-review audit log. The MVP runs synchronously in-process.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from worker import agent_orchestrator as ao
from worker import venues as venue_mod
from worker.classify import classify_text
from worker.extraction import extract_manuscript
from worker.external_prompt_manager import generate_prompts
from worker.markdown_store import append_line, now_iso, read_text, read_yaml, write_text, write_yaml
from worker.paths import load_config, review_dir

MODES = [
    "init", "ingest", "validate_upload", "extract", "classify", "scan_venues",
    "discover_venues", "venue_fit", "timeline", "desk_reject_precheck",
    "literature_queries", "generate_external_prompts", "import_external_responses",
    "review", "specialized_review", "integrity", "editorial_decision",
    "export", "full_review",
]


@dataclass
class PipelineResult:
    review_id: str
    mode: str
    steps: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "review_id": self.review_id,
            "mode": self.mode,
            "steps": self.steps,
            "outputs": self.outputs,
            "warnings": self.warnings,
        }


# --------------------------------------------------------------------------- #
# State helpers
# --------------------------------------------------------------------------- #
def _meta_path(review_id: str) -> Path:
    return review_dir(review_id) / "metadata.yaml"


def _load_meta(review_id: str) -> dict:
    return read_yaml(_meta_path(review_id))


def _save_meta(review_id: str, meta: dict) -> None:
    meta["updated_at"] = now_iso()
    write_yaml(_meta_path(review_id), meta)


def _audit(review_id: str, message: str) -> None:
    append_line(review_dir(review_id) / "audit" / "audit_log.md", f"- {now_iso()} — {message}")
    try:
        from worker.db import log_audit
        log_audit(review_id, "pipeline", message)
    except Exception:
        pass


def _set_status(review_id: str, status: str, step: int | None = None) -> None:
    try:
        from sqlalchemy import select

        from worker.db import Review, session_scope
        with session_scope() as s:
            r = s.scalar(select(Review).where(Review.review_id == review_id))
            if r is not None:
                r.status = status
                if step is not None:
                    r.current_step = step
    except Exception:
        pass


def _record_agent_run(out: ao.AgentOutput, review_id: str, output_path: Path) -> None:
    try:
        from worker.db import InternalAgentRun, session_scope
        with session_scope() as s:
            s.add(InternalAgentRun(
                review_id=review_id, venue_id=out.venue_id, agent_id=out.agent_id,
                reviewer_profile=out.reviewer_profile, engine=out.engine, model=out.model,
                mode=out.mode, output_path=str(output_path), status="completed",
            ))
    except Exception:
        pass
    append_line(
        review_dir(review_id) / "audit" / "model_usage.md",
        f"| {now_iso()} | {out.agent_id} | {out.engine} | {out.model} | {out.mode} |",
    )


def _selected_venues(review_id: str, meta: dict) -> list[str]:
    selected = meta.get("selected_venues") or []
    if selected:
        return selected
    # Auto-select the top discovered candidate so the pipeline can proceed.
    candidates = venue_mod.discover_venues(review_id, meta.get("likely_venue_families", []))
    if candidates:
        return [candidates[0]["venue_id"]]
    return []


def _enabled_specialized(meta: dict) -> list[str]:
    cfg = load_config("reviewer_profiles")
    detected = set(meta.get("detected_areas", []))
    enabled = []
    for p in cfg.get("specialized_reviewers", []):
        if set(p.get("activation_areas", [])) & detected:
            enabled.append(p["id"])
    return enabled


def _main_reviewers() -> list[str]:
    """Default main reviewers = those marked default_enabled (the 3 core ones)."""
    cfg = load_config("reviewer_profiles")
    return [p["id"] for p in cfg.get("main_reviewers", []) if p.get("default_enabled", True)]


# --------------------------------------------------------------------------- #
# Mode handlers
# --------------------------------------------------------------------------- #
def _latest_manuscript(review_id: str) -> Path | None:
    original = review_dir(review_id) / "input" / "original"
    latex = review_dir(review_id) / "input" / "latex_source"
    candidates = []
    if original.exists():
        candidates += [p for p in original.iterdir() if p.is_file()]
    if latex.exists():
        candidates += list(latex.rglob("*.tex"))
    if not candidates:
        return None
    # Prefer LaTeX > md > docx > pdf.
    priority = {".tex": 0, ".md": 1, ".markdown": 1, ".docx": 2, ".pdf": 3}
    candidates.sort(key=lambda p: priority.get(p.suffix.lower(), 9))
    return candidates[0]


def _do_extract(review_id: str, result: PipelineResult) -> None:
    src = _latest_manuscript(review_id)
    if src is None:
        result.warnings.append("No manuscript uploaded yet; skipping extraction.")
        return
    extraction = extract_manuscript(review_id, src)
    result.outputs.append("extracted/manuscript_extracted.md")
    result.outputs.append("extracted/paper_extraction.json")
    result.warnings.extend(extraction.warnings)
    _audit(review_id, f"extracted manuscript ({extraction.source_format})")


def _do_classify(review_id: str, result: PipelineResult) -> None:
    md_path = review_dir(review_id) / "extracted" / "manuscript_extracted.md"
    text = read_text(md_path) if md_path.exists() else ""
    cls = classify_text(text)
    meta = _load_meta(review_id)
    meta["detected_areas"] = cls.detected_areas
    meta["detected_area_labels"] = cls.detected_area_labels
    meta["paper_type"] = cls.paper_type
    meta["likely_venue_families"] = cls.likely_venue_families
    # Auto-identify the title from the manuscript (so the user need not type it).
    fields = read_yaml(review_dir(review_id) / "extracted" / "paper_extraction.json").get("fields", {})
    extracted_title = (fields.get("title") or "").strip()
    meta["extracted_title"] = extracted_title or "NEEDS_USER_INPUT"
    if extracted_title and extracted_title not in ("NEEDS_USER_INPUT", "UNKNOWN") and \
            (meta.get("title") in (None, "", "UNKNOWN")):
        meta["title"] = extracted_title[:300]
    _save_meta(review_id, meta)
    write_text(
        review_dir(review_id) / "extracted" / "classification.md",
        "# Area & paper type\n\n"
        f"- Paper type: {cls.paper_type}\n"
        f"- Detected areas: {', '.join(cls.detected_area_labels) or 'UNKNOWN'}\n"
        f"- Likely venue families: {', '.join(map(str, cls.likely_venue_families)) or 'UNKNOWN'}\n",
    )
    # Mirror to DB.
    try:
        from sqlalchemy import select
        from worker.db import Review, session_scope
        with session_scope() as s:
            r = s.scalar(select(Review).where(Review.review_id == review_id))
            if r is not None:
                r.paper_type = cls.paper_type
                r.detected_areas = ", ".join(cls.detected_area_labels)
                if meta.get("title"):
                    r.title = meta["title"]
    except Exception:
        pass
    result.outputs.append("extracted/classification.md")
    _audit(review_id, f"classified: {cls.paper_type}; areas={cls.detected_areas}")


def _do_discover(review_id: str, result: PipelineResult) -> None:
    meta = _load_meta(review_id)
    ranked = venue_mod.discover_venues(review_id, meta.get("likely_venue_families", []))
    lines = [f"# Candidate venues — {review_id}", "", f"_Generated {now_iso()}_", "",
             "| score | venue_id | name | Q1 access | quartile/rank | speed | rigor |",
             "| ---: | --- | --- | --- | --- | --- | --- |"]
    for r in ranked[:30]:
        lines.append(
            f"| {r['score']} | {r['venue_id']} | {r['name']} | {r['q1_accessibility_class']} | "
            f"{r['quartile_or_rank']} | {r['publication_speed_category']} | {r['review_rigor']} |"
        )
    write_text(review_dir(review_id) / "venues" / "candidate_venues.md", "\n".join(lines))
    result.outputs.append("venues/candidate_venues.md")
    _audit(review_id, f"discovered {len(ranked)} candidate venues")


def _do_reviews(review_id: str, result: PipelineResult, specialized: bool) -> None:
    meta = _load_meta(review_id)
    venue_ids = _selected_venues(review_id, meta)
    if not venue_ids:
        result.warnings.append("No venues available; skipping reviews.")
        return
    profiles = _enabled_specialized(meta) if specialized else _main_reviewers()
    subdir = "specialized" if specialized else "internal"
    for venue_id in venue_ids:
        for profile_id in profiles:
            out = ao.run_reviewer(review_id, venue_id, profile_id)
            path = review_dir(review_id) / "reviewer_outputs" / subdir / f"{venue_id}__{profile_id}.md"
            write_text(path, out.markdown)
            _record_agent_run(out, review_id, path)
            result.outputs.append(str(path.relative_to(review_dir(review_id))))
    _audit(review_id, f"ran {'specialized' if specialized else 'main'} reviewers for {venue_ids}")


def _do_integrity(review_id: str, result: PipelineResult) -> None:
    meta = _load_meta(review_id)
    venue_ids = _selected_venues(review_id, meta)
    venue_id = venue_ids[0] if venue_ids else ""
    out = ao.run_integrity(review_id, venue_id)
    path = review_dir(review_id) / "reviewer_outputs" / "integrity_ai_use_audit.md"
    write_text(path, out.markdown)
    _record_agent_run(out, review_id, path)
    result.outputs.append("reviewer_outputs/integrity_ai_use_audit.md")
    _audit(review_id, "ran integrity / AI-use audit")


def _do_editor(review_id: str, result: PipelineResult) -> None:
    meta = _load_meta(review_id)
    venue_ids = _selected_venues(review_id, meta)
    venue_id = venue_ids[0] if venue_ids else ""
    rev_dir = review_dir(review_id) / "reviewer_outputs"
    reviewer_files = list((rev_dir / "internal").glob("*.md")) + list((rev_dir / "specialized").glob("*.md"))
    out = ao.run_editor(review_id, venue_id, reviewer_files)
    editor_dir = review_dir(review_id) / "editor"
    write_text(editor_dir / "editor_decision.md", out.markdown)
    write_text(editor_dir / "meta_review.md",
               f"# Meta review — {review_id}\n\nSynthesis of reviewer reports (do not average). NEEDS_USER_INPUT.\n")
    write_text(editor_dir / "revision_plan.md",
               f"# Revision plan — {review_id}\n\n## Mandatory revisions\n- NEEDS_USER_INPUT\n\n## Optional improvements\n- NEEDS_USER_INPUT\n")
    write_text(editor_dir / "rebuttal_strategy.md",
               f"# Rebuttal strategy — {review_id}\n\n- NEEDS_USER_INPUT\n")
    write_text(editor_dir / "final_letter.md",
               f"# Final letter — {review_id}\n\nDear authors,\n\nNEEDS_USER_INPUT\n")
    _record_agent_run(out, review_id, editor_dir / "editor_decision.md")
    result.outputs += [
        "editor/editor_decision.md", "editor/meta_review.md", "editor/revision_plan.md",
        "editor/rebuttal_strategy.md", "editor/final_letter.md",
    ]
    _audit(review_id, "generated editor decision package")


def _do_external_prompts(review_id: str, result: PipelineResult) -> None:
    meta = _load_meta(review_id)
    venue_ids = _selected_venues(review_id, meta)
    if not venue_ids:
        result.warnings.append("No venues available; skipping external prompts.")
        return
    profiles = _main_reviewers() + _enabled_specialized(meta)
    generated = generate_prompts(review_id, venue_ids, profiles)
    # Index in DB.
    try:
        from worker.db import ExternalPrompt, session_scope
        with session_scope() as s:
            for g in generated:
                s.add(ExternalPrompt(
                    review_id=review_id, venue_id=g.venue_id, reviewer_profile=g.reviewer_profile,
                    engine=g.engine, prompt_file_path=str(g.prompt_path),
                    expected_response_filename=g.expected_response_filename,
                ))
    except Exception:
        pass
    result.outputs.append("external_prompts/index.md")
    _audit(review_id, f"generated {len(generated)} external prompts")


def _do_literature_queries(review_id: str, result: PipelineResult) -> None:
    meta = _load_meta(review_id)
    areas = ", ".join(meta.get("detected_area_labels", [])) or "UNKNOWN"
    body = (
        f"# Literature queries — {review_id}\n\n"
        f"_Areas: {areas}_\n\n"
        "Generate real results in Perplexity / Scholar / Semantic Scholar and paste them under "
        "literature/notes/. Do not invent results.\n\n"
        "## Suggested query buckets\n"
        "- Most recent papers (last 2 years)\n- Foundational papers\n- Surveys / systematic reviews\n"
        "- Datasets and benchmarks\n- Competing methods\n- Criticisms / limitations of the approach\n"
    )
    write_text(review_dir(review_id) / "literature" / "perplexity_queries.md", body)
    # Empty literature matrix template.
    write_text(
        review_dir(review_id) / "literature" / "literature_matrix.csv",
        "citation_key,title,year,venue,authors,problem,method,dataset,metrics,key_result,"
        "relation_to_current_paper,difference_from_current_paper,supports_claim,challenges_claim,notes\n",
    )
    result.outputs.append("literature/perplexity_queries.md")
    _audit(review_id, "generated literature query template")


def _do_export(review_id: str, result: PipelineResult) -> None:
    from worker.exporters import export_review_package
    info = export_review_package(review_id)
    result.outputs.append("exports/full_review_package.zip")
    if not info["pdf_rendered"]:
        result.warnings.append("PDF engine not available; exported Markdown only (best-effort PDF).")
    _audit(review_id, "exported final review package")


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
def run_pipeline(review_id: str, mode: str) -> PipelineResult:
    if mode not in MODES:
        raise ValueError(f"Unknown mode '{mode}'. Valid modes: {', '.join(MODES)}")
    result = PipelineResult(review_id=review_id, mode=mode)
    _set_status(review_id, f"running:{mode}")

    sequence = load_config("pipeline").get("full_review_sequence", []) if mode == "full_review" else [mode]

    for step in sequence:
        result.steps.append(step)
        _mark_running(review_id, step)
        if step in ("init", "ingest", "validate_upload"):
            _audit(review_id, f"{step}: no-op (handled at upload time)")
        elif step == "extract":
            _do_extract(review_id, result)
        elif step == "classify":
            _do_classify(review_id, result)
        elif step == "scan_venues":
            n = venue_mod.scan_venue_markdowns()
            _audit(review_id, f"indexed {n} venues")
        elif step == "discover_venues":
            _do_discover(review_id, result)
        elif step == "venue_fit":
            meta = _load_meta(review_id)
            venue_mod.write_venue_fit_report(review_id, _selected_venues(review_id, meta))
            result.outputs.append("venues/venue_fit_report.md")
        elif step == "timeline":
            meta = _load_meta(review_id)
            venue_mod.write_timeline_report(review_id, _selected_venues(review_id, meta))
            result.outputs.append("venues/venue_timeline_report.md")
        elif step == "desk_reject_precheck":
            venue_mod.write_desk_reject_precheck(review_id)
            result.outputs.append("venues/desk_reject_precheck.md")
        elif step == "literature_queries":
            _do_literature_queries(review_id, result)
        elif step == "generate_external_prompts":
            _do_external_prompts(review_id, result)
        elif step == "import_external_responses":
            _audit(review_id, "import_external_responses: use the upload endpoint/CLI to add responses")
        elif step == "review":
            _do_reviews(review_id, result, specialized=False)
        elif step == "specialized_review":
            _do_reviews(review_id, result, specialized=True)
        elif step == "integrity":
            _do_integrity(review_id, result)
        elif step == "editorial_decision":
            _do_editor(review_id, result)
        elif step == "export":
            _do_export(review_id, result)

    _set_status(review_id, f"done:{mode}")
    _update_meta_status(review_id, mode)
    _audit(review_id, f"pipeline mode '{mode}' completed")
    return result


def _extract_decision(review_id: str) -> str | None:
    """Parse the editor's final decision = the first line after the Decision header.

    Only the decision line is inspected (not the rationale), so phrases like
    "major revision rather than desk reject" don't mis-resolve to desk reject.
    """
    p = review_dir(review_id) / "editor" / "editor_decision.md"
    if not p.exists():
        return None
    text = read_text(p)
    m = re.search(r"(?im)^#+\s*decision\s*:?\s*$", text)
    after = text[m.end():] if m else ""
    first = ""
    for ln in after.splitlines():
        s = ln.strip().strip("*>#`").strip()
        if s:
            first = s.lower()
            break
    if not first or "needs_user_input" in first:
        return None  # template scaffold — no real decision yet
    for d in ("desk reject", "major revision", "minor revision", "accept", "reject"):
        if d in first:
            return d
    return None


_STEP_NUM = {
    "extract": 2, "classify": 3, "scan_venues": 4, "discover_venues": 4, "venue_fit": 4,
    "timeline": 4, "desk_reject_precheck": 5, "generate_external_prompts": 7,
    "review": 9, "specialized_review": 9, "integrity": 10, "editorial_decision": 11,
    "export": 13,
}


def _mark_running(review_id: str, step: str) -> None:
    """Lightweight per-step progress so the UI can show live status."""
    try:
        meta = _load_meta(review_id)
        meta["status"] = f"running:{step}"
        sn = _STEP_NUM.get(step)
        if sn is not None:
            meta["current_step"] = max(int(meta.get("current_step", 0) or 0), sn)
        _save_meta(review_id, meta)
    except Exception:
        pass


def _update_meta_status(review_id: str, mode: str) -> None:
    """Reflect pipeline progress in metadata.yaml (drives the UI status)."""
    meta = _load_meta(review_id)
    step_for_mode = {
        "extract": 2, "classify": 3, "discover_venues": 4, "venue_fit": 4,
        "generate_external_prompts": 7, "review": 9, "specialized_review": 9,
        "integrity": 10, "editorial_decision": 11, "export": 13, "full_review": 13,
    }.get(mode)
    if step_for_mode is not None:
        meta["current_step"] = max(int(meta.get("current_step", 0) or 0), step_for_mode)
    if mode in ("full_review", "export", "editorial_decision"):
        meta["status"] = "completed"
        dec = _extract_decision(review_id)
        if dec:
            meta["final_decision"] = dec
    else:
        meta["status"] = f"done:{mode}"
    _save_meta(review_id, meta)
    # Mirror final_decision into the DB.
    try:
        from sqlalchemy import select
        from worker.db import Review, session_scope
        with session_scope() as s:
            r = s.scalar(select(Review).where(Review.review_id == review_id))
            if r is not None:
                if meta.get("final_decision"):
                    r.final_decision = meta["final_decision"]
                r.current_step = meta.get("current_step", r.current_step)
    except Exception:
        pass
