"""Unit tests for core worker utilities."""
from __future__ import annotations

import io
import re
import zipfile

from worker.classify import classify_text
from worker.extraction import detect_input_format, extract_manuscript
from worker.file_ingestion import ingest_file
from worker.markdown_store import slugify
from worker.review_id import create_review_tree, new_review_id
from worker.reviews import create_review


def test_review_id_format():
    rid = new_review_id()
    assert re.match(r"^REV-\d{8}-\d{6}-[A-Z0-9]{6}$", rid)


def test_create_review_tree_creates_layout():
    rid = new_review_id()
    root = create_review_tree(rid, title="X")
    assert (root / "metadata.yaml").exists()
    for sub in ("input/original", "extracted", "venues", "editor", "exports", "audit"):
        assert (root / sub).exists()
    assert (root / "audit" / "audit_log.md").exists()


def test_slugify():
    assert slugify("Journal of Systems Architecture") == "journal-of-systems-architecture"
    assert slugify("Data in Brief!") == "data-in-brief"
    assert slugify("") == "item"


def test_classify_detects_fas_area():
    text = "face anti-spoofing presentation attack detection APCER BPCER spatiotemporal"
    cls = classify_text(text)
    assert "fas_biometrics_security" in cls.detected_areas
    assert 4 in cls.likely_venue_families


def test_classify_empty_is_unknown():
    cls = classify_text("the quick brown fox")
    assert cls.detected_areas == []
    assert cls.paper_type == "UNKNOWN"


def test_extraction_from_markdown(repo_root):
    info = create_review(title="extract test")
    src = repo_root / "tests" / "sample_paper" / "manuscript.md"
    assert detect_input_format(src) == "markdown"
    result = extract_manuscript(info.review_id, src)
    assert "Face Anti-Spoofing" in result.fields["title"]
    assert result.fields["abstract"] != "NEEDS_USER_INPUT"


def test_ingest_rejects_bad_extension():
    info = create_review(title="upload test")
    res = ingest_file(info.review_id, original_filename="evil.exe", data=b"MZ", kind="manuscript")
    assert res.ok is False
    assert any("not allowed" in e for e in res.errors)


def test_ingest_accepts_markdown_and_hashes():
    info = create_review(title="upload md")
    res = ingest_file(info.review_id, original_filename="m.md", data=b"# Title\n", kind="manuscript")
    assert res.ok is True
    assert len(res.sha256) == 64
    assert res.stored_path is not None


def test_zip_path_traversal_blocked():
    info = create_review(title="zip test")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("main.tex", "\\documentclass{article}\\begin{document}hi\\end{document}")
        zf.writestr("../evil.txt", "pwned")
    res = ingest_file(info.review_id, original_filename="src.zip", data=buf.getvalue(), kind="manuscript")
    # The good file extracts; the traversal entry is reported as an error.
    assert any("traversal" in e.lower() or "unsafe" in e.lower() for e in res.errors)
