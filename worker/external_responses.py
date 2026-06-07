"""Import external AI responses (Step 8).

Converts PDF/DOCX to Markdown if needed, validates the review ID, detects the
engine / reviewer / venue from the filename, writes a short summary and updates
the responses index.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from worker.extraction import extract_from_docx, extract_from_pdf
from worker.external_prompt_manager import ENGINES
from worker.markdown_store import append_line, now_iso, slugify, write_text
from worker.paths import review_dir

_PROFILE_HINTS = [
    "reviewer-methodology", "reviewer-domain", "reviewer-systems-architecture",
    "reviewer-reproducibility", "reviewer-scientific-impact", "reviewer-document-ai-htr",
    "reviewer-education-research", "reviewer-dataset-benchmark", "reviewer-spectral-agri-food",
    "reviewer-fas-biometrics-security", "reviewer-cloud-hpc-scheduling",
]


@dataclass
class ResponseImport:
    review_id: str
    venue_id: str
    reviewer_profile: str
    engine: str
    stored_path: str
    has_sources: bool
    looks_incomplete: bool
    warnings: list[str]


def _to_markdown(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".md", ".markdown", ".txt"):
        return data.decode("utf-8", errors="replace")
    # For PDF/DOCX we must persist to a temp file for the libraries.
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as fh:
        fh.write(data)
        tmp_path = Path(fh.name)
    try:
        if ext == ".pdf":
            return extract_from_pdf(tmp_path)
        if ext == ".docx":
            return extract_from_docx(tmp_path)
        return data.decode("utf-8", errors="replace")
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass


def _detect(filename: str, content: str, review_id: str) -> tuple[str, str, str]:
    low = filename.lower()
    engine = next((e for e in ENGINES if e in low), "UNKNOWN")
    profile = next((p for p in _PROFILE_HINTS if p in low), "UNKNOWN")
    # venue id: look for "__<venue>__" pattern from our expected filename scheme.
    m = re.search(re.escape(review_id) + r"__([a-z0-9\-]+)__", filename)
    venue_id = m.group(1) if m else "UNKNOWN"
    if engine == "UNKNOWN":
        m2 = re.search(r"\b(chatgpt|claude|gemini|perplexity|notebooklm)\b", content.lower())
        if m2:
            engine = m2.group(1)
    return venue_id, profile, engine


def import_response(review_id: str, *, filename: str, data: bytes) -> ResponseImport:
    warnings: list[str] = []
    content = _to_markdown(filename, data)

    if review_id not in filename and review_id not in content:
        warnings.append(f"Review ID '{review_id}' not found in filename or content.")

    venue_id, profile, engine = _detect(filename, content, review_id)
    has_sources = bool(re.search(r"https?://", content))
    looks_incomplete = len(content.strip()) < 200 or "NEEDS_USER_INPUT" in content

    venue_dir = review_dir(review_id) / "external_responses" / "by_venue" / (venue_id or "UNKNOWN")
    venue_dir.mkdir(parents=True, exist_ok=True)
    safe = f"{slugify(Path(filename).stem)}.md"
    stored = venue_dir / safe
    write_text(stored, content)

    # Short summary alongside the raw response.
    summary = "\n".join([
        f"# Imported external response — {filename}",
        "",
        f"- review_id: {review_id}",
        f"- venue_id: {venue_id}",
        f"- reviewer_profile: {profile}",
        f"- engine: {engine}",
        f"- has_sources: {has_sources}",
        f"- looks_incomplete: {looks_incomplete}",
        f"- imported_at: {now_iso()}",
        "",
        "## First lines",
        "",
        "\n".join(content.splitlines()[:15]),
    ])
    write_text(venue_dir / f"{slugify(Path(filename).stem)}_summary.md", summary)

    # Update index.
    index = review_dir(review_id) / "external_responses" / "index.md"
    if not index.exists():
        write_text(index, f"# External responses index — {review_id}\n\n| venue | reviewer | engine | file | sources | incomplete |\n| --- | --- | --- | --- | --- | --- |\n")
    append_line(index, f"| {venue_id} | {profile} | {engine} | {stored.name} | {has_sources} | {looks_incomplete} |")

    # DB index (best-effort).
    try:
        from worker.db import ExternalResponse, session_scope
        with session_scope() as s:
            s.add(ExternalResponse(
                review_id=review_id, venue_id=venue_id, reviewer_profile=profile, engine=engine,
                response_file_path=str(stored), has_sources=has_sources, looks_incomplete=looks_incomplete,
            ))
    except Exception:
        pass

    return ResponseImport(review_id, venue_id, profile, engine, str(stored), has_sources, looks_incomplete, warnings)
