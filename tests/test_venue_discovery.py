"""Tests for the venue-discovery importer (the emphasized feature).

Exercises both real seed files: a Markdown pipe-table and a messy CSV with
unbalanced quotes + cp1252-ish accents.
"""
from __future__ import annotations

from worker import venue_discovery as vd
from worker.markdown_store import read_yaml
from worker.paths import venues_dir
from conftest import VENUE_FILE_1, VENUE_FILE_2


def test_detect_format():
    assert vd.detect_format("| a | b |\n|---|---|\n| 1 | 2 |") == "markdown_table"
    assert vd.detect_format("V1,foo,bar") == "csv"


def test_parse_markdown_table():
    text = VENUE_FILE_1.read_text(encoding="utf-8")
    fmt, records = vd.parse_source(text)
    assert fmt == "markdown_table"
    assert len(records) == 22
    assert records[0]["acronym"] == "TPDS"


def test_parse_messy_csv():
    fmt, records = vd.parse_source(vd.smart_decode(VENUE_FILE_2.read_bytes()))
    assert fmt == "csv"
    # 15 venue rows (V21..V35) despite unbalanced quotes.
    assert len(records) == 15
    assert records[0]["acronym"] == "JSA"


def test_stable_venue_id_and_collision():
    used: set[str] = set()
    a, c1 = vd.stable_venue_id({"acronym": "JSA", "name": "Journal of Systems Architecture"}, used)
    assert a == "jsa" and c1 is False
    b, c2 = vd.stable_venue_id({"acronym": "JSA", "name": "Another"}, used)
    assert b == "jsa-2" and c2 is True


def test_import_preserves_unverified_and_writes_docs():
    # Import both batches into the isolated temp venues dir.
    used: set[str] = set()
    r1 = vd.import_bytes(VENUE_FILE_1.read_bytes(), source_name="f1.csv", index_in_db=False, used_ids=used)
    r2 = vd.import_bytes(VENUE_FILE_2.read_bytes(), source_name="f2.csv", index_in_db=False, used_ids=used)
    assert len(r1.venues) == 22
    assert len(r2.venues) == 15
    # Stable IDs avoided overwrites across the two batches.
    total_dirs = list((venues_dir() / "journals").glob("*/venue_profile.yaml"))
    assert len(total_dirs) >= 36

    # A CSV-sourced venue mapped correctly and kept "not verified" verbatim.
    profile = read_yaml(venues_dir() / "journals" / "jsa" / "venue_profile.yaml")
    assert profile["name"] == "Journal of Systems Architecture"
    assert profile["source_ref"].startswith("V21 from")
    tl = profile["publication_timeline"]
    assert tl["time_to_first_decision"] == "not verified"


def test_smart_decode_handles_accents():
    # diseño encoded as UTF-8 bytes should round-trip.
    assert vd.smart_decode("diseño".encode("utf-8")) == "diseño"
    # cp1252 bytes for ñ (0xf1) decode without raising.
    assert "o" in vd.smart_decode(b"dise\xf1o")
