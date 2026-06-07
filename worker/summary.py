"""Build a readable results summary for a review.

Parses each reviewer output and the editor decision into a compact digest:
recommendation, confidence, engine/mode and a short summary — so the UI can
show "the answer of each reviewer and the editor" at a glance instead of raw
Markdown.
"""
from __future__ import annotations

import re

from worker.markdown_store import read_text
from worker.paths import review_dir


def _meta_field(text: str, field: str) -> str:
    m = re.search(rf"(?im)^[-*]\s*{re.escape(field)}\s*:\s*(.+)$", text)
    return m.group(1).strip() if m else ""


def _section(text: str, header: str) -> str:
    m = re.search(rf"(?ims)^#+\s*{re.escape(header)}\s*$(.*?)(?=^#+\s|\Z)", text)
    return m.group(1).strip() if m else ""


def _first_line(text: str) -> str:
    for ln in (text or "").splitlines():
        s = ln.strip().lstrip("#").strip()
        if s:
            return s
    return ""


def _first_para(text: str, limit: int = 500) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    if not paras:
        return ""
    return re.sub(r"\s+", " ", paras[0])[:limit]


def _reviewer_entry(text: str, kind: str, relpath: str, name: str) -> dict:
    return {
        "name": name,
        "kind": kind,
        "engine": _meta_field(text, "engine") or "—",
        "mode": _meta_field(text, "mode") or "—",
        "recommendation": _first_line(_section(text, "Recommendation")) or "—",
        "confidence": _meta_field(text, "confidence") or "—",
        "summary": _first_para(_section(text, "Short summary") or _section(text, "Summary")),
        "relpath": relpath,
        "is_real": _meta_field(text, "mode") == "autonomous",
    }


def review_summary(review_id: str) -> dict:
    root = review_dir(review_id)
    reviewers: list[dict] = []
    for kind, sub in (("internal", "reviewer_outputs/internal"),
                      ("specialized", "reviewer_outputs/specialized")):
        d = root / sub
        if d.exists():
            for f in sorted(d.glob("*.md")):
                text = read_text(f)
                name = f.stem.split("__")[-1] if "__" in f.stem else f.stem
                rel = str(f.relative_to(root)).replace("\\", "/")
                reviewers.append(_reviewer_entry(text, kind, rel, name))

    integ_path = root / "reviewer_outputs" / "integrity_ai_use_audit.md"
    integrity = None
    if integ_path.exists():
        text = read_text(integ_path)
        integrity = {
            "engine": _meta_field(text, "engine") or "—",
            "mode": _meta_field(text, "mode") or "—",
            "relpath": "reviewer_outputs/integrity_ai_use_audit.md",
        }

    ed_path = root / "editor" / "editor_decision.md"
    editor = {"exists": ed_path.exists(), "relpath": "editor/editor_decision.md",
              "decision": "—", "engine": "—", "mode": "—"}
    if ed_path.exists():
        from worker.pipeline_runner import _extract_decision
        text = read_text(ed_path)
        editor.update({
            "decision": (_extract_decision(review_id) or "—"),
            "engine": _meta_field(text, "engine") or "—",
            "mode": _meta_field(text, "mode") or "—",
        })

    return {
        "review_id": review_id,
        "reviewers": reviewers,
        "integrity": integrity,
        "editor": editor,
    }
