"""Export assembly: copy editorial artefacts into exports/ and zip them.

PDF rendering is best-effort (plan deviation D10): Markdown is always emitted;
a PDF is produced only when a rendering engine is available.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from worker.markdown_store import now_iso, read_text, write_text
from worker.paths import review_dir


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return True
    return False


def try_render_pdf(md_path: Path, pdf_path: Path) -> bool:
    """Best-effort Markdown -> PDF. Returns True on success."""
    # Strategy 1: markdown -> HTML -> PDF via weasyprint, if installed.
    try:
        import markdown as md_lib  # type: ignore
        from weasyprint import HTML  # type: ignore

        html = md_lib.markdown(read_text(md_path), extensions=["tables", "fenced_code"])
        HTML(string=html).write_pdf(str(pdf_path))
        return True
    except Exception:
        return False


def export_review_package(review_id: str) -> dict:
    root = review_dir(review_id)
    exports = root / "exports"
    exports.mkdir(parents=True, exist_ok=True)

    mapping = {
        root / "editor" / "editor_decision.md": exports / "final_editor_decision.md",
        root / "editor" / "revision_plan.md": exports / "revision_plan.md",
        root / "editor" / "rebuttal_strategy.md": exports / "rebuttal_letter_draft.md",
        root / "venues" / "venue_fit_report.md": exports / "venue_fit_report.md",
        root / "audit" / "audit_log.md": exports / "audit_log.md",
    }
    copied = []
    for src, dst in mapping.items():
        if _copy_if_exists(src, dst):
            copied.append(dst.name)

    # Reviewer response matrix (placeholder if none exists yet).
    matrix = exports / "reviewer_response_matrix.md"
    if not matrix.exists():
        write_text(matrix, _default_response_matrix(review_id))
        copied.append(matrix.name)

    # Best-effort PDF of the decision.
    pdf_ok = False
    decision_md = exports / "final_editor_decision.md"
    if decision_md.exists():
        pdf_ok = try_render_pdf(decision_md, exports / "final_editor_decision.pdf")

    # Zip everything in exports/.
    zip_path = exports / "full_review_package.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(exports.glob("*")):
            if f.name == zip_path.name:
                continue
            zf.write(f, arcname=f.name)

    return {
        "review_id": review_id,
        "exported_at": now_iso(),
        "files": copied,
        "pdf_rendered": pdf_ok,
        "package": str(zip_path),
    }


def _default_response_matrix(review_id: str) -> str:
    return (
        f"# Reviewer response matrix — {review_id}\n\n"
        "| reviewer_id | comment_id | original_comment | author_response | claimed_change | "
        "manuscript_section | status | evidence_in_new_manuscript | remaining_risk |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| NEEDS_USER_INPUT | | | | | | | | |\n"
    )
