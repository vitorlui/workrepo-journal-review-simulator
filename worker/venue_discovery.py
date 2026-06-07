"""Venue-discovery importer.

Ingests a Perplexity venue response (Markdown pipe-table **or** CSV — detected
by content, not extension) and materialises each venue into the documental
memory under ``data/global_knowledge/venues/journals/<venue_id>/`` plus a
normalized ``processed/`` snapshot and an ``import_reports/`` report.

Key behaviours (plan deviations A1/A2 + critical rules):
* Stable ``venue_id`` derived from acronym/name (never the raw ``V#``), so the
  ``V21/V22`` collisions across the two seed files don't overwrite each other.
* The original ``V#`` + source filename are kept as ``source_ref``.
* Values are preserved verbatim — ``not verified`` / ``UNKNOWN`` are never
  replaced with invented metrics.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from worker.markdown_store import now_iso, slugify, write_json, write_text, write_yaml
from worker.paths import global_knowledge_dir, load_config, venues_dir


@dataclass
class VenueRecord:
    venue_id: str
    source_ref: str
    raw: dict
    path_on_disk: str = ""


@dataclass
class ImportResult:
    source: str
    detected_format: str
    venues: list[VenueRecord] = field(default_factory=list)
    skipped: int = 0
    collisions_resolved: int = 0
    warnings: list[str] = field(default_factory=list)
    report_path: str = ""
    processed_csv: str = ""
    processed_json: str = ""


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def _columns() -> list[str]:
    return load_config("venue_discovery").get("columns", [])


def smart_decode(data: bytes) -> str:
    """Decode venue bytes tolerantly.

    Perplexity exports are sometimes cp1252/latin-1 (accented Spanish text)
    rather than UTF-8. Try the most likely encodings before giving up.
    """
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def detect_format(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "empty"
    pipe_lines = sum(1 for ln in lines if ln.lstrip().startswith("|"))
    if pipe_lines >= max(2, int(0.3 * len(lines))):
        return "markdown_table"
    return "csv"


def _is_separator_row(cells: list[str]) -> bool:
    joined = "".join(cells)
    return bool(joined) and set(joined) <= set("-:| ")


def _parse_markdown_table(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if _is_separator_row(cells):
            continue
        rows.append(cells)
    return rows  # first row is the header


def _parse_csv(text: str) -> list[list[str]]:
    """Parse a venue CSV robustly.

    Real Perplexity CSV exports can have unbalanced quotes (e.g. a ``notes``
    field that opens a quote but never closes it before the next row). A naive
    ``csv.reader`` then bleeds many rows into one. We instead split the data
    section into records at each ``^V<number>,`` line boundary, balance quotes
    per record, and parse each record individually.
    """
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^V\d+\s*,", ln)), None)
    if start is None:
        # No "V#" ids: fall back to a plain reader (balanced CSV).
        rows = []
        for row in csv.reader(io.StringIO(text)):
            if any(c.strip() for c in row):
                rows.append([c.strip() for c in row])
        return rows

    data = "\n".join(lines[start:])
    records = re.split(r"(?m)(?=^V\d+\s*,)", data)
    rows: list[list[str]] = []
    for rec in records:
        rec = rec.strip()
        if not rec:
            continue
        if rec.count('"') % 2 == 1:  # repair an unterminated quoted field
            rec += '"'
        try:
            parsed = next(csv.reader(io.StringIO(rec)))
        except StopIteration:
            continue
        rows.append([c.strip() for c in parsed])
    return rows


def _looks_like_data_row(first_cell: str) -> bool:
    return bool(re.match(r"^V\d+$", first_cell.strip()))


def parse_source(text: str) -> tuple[str, list[dict]]:
    """Return (detected_format, list of raw column->value dicts)."""
    columns = _columns()
    fmt = detect_format(text)
    records: list[dict] = []

    if fmt == "markdown_table":
        rows = _parse_markdown_table(text)
        data_rows = rows[1:] if rows else []  # skip header
        for cells in data_rows:
            if not cells or not cells[0].strip():
                continue
            record = {columns[i]: (cells[i] if i < len(cells) else "") for i in range(len(columns))}
            records.append(record)
    elif fmt == "csv":
        rows = _parse_csv(text)
        for cells in rows:
            if not cells or not _looks_like_data_row(cells[0]):
                continue
            record = {columns[i]: (cells[i] if i < len(cells) else "") for i in range(len(columns))}
            records.append(record)
    return fmt, records


# --------------------------------------------------------------------------- #
# Mapping -> venue_profile.yaml
# --------------------------------------------------------------------------- #
def _split_list(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[;,]", value)
    return [p.strip() for p in parts if p.strip()]


def _family_labels(value: str) -> list[str]:
    fam_map = load_config("venue_discovery").get("family_map", {})
    labels = []
    for code in _split_list(value):
        labels.append(fam_map.get(code, code))
    return labels


def stable_venue_id(raw: dict, used: set[str]) -> tuple[str, bool]:
    acronym = (raw.get("acronym") or "").strip()
    name = (raw.get("name") or "").strip()
    base = acronym if acronym and acronym.upper() not in {"UNKNOWN", "N/A"} else name
    slug = slugify(base or name or "venue")
    collision = False
    candidate = slug
    i = 2
    while candidate in used:
        collision = True
        candidate = f"{slug}-{i}"
        i += 1
    used.add(candidate)
    return candidate, collision


def _build_profile(venue_id: str, source_ref: str, raw: dict, source_name: str) -> dict:
    def g(key: str) -> str:
        return (raw.get(key) or "").strip() or "UNKNOWN"

    return {
        "venue_id": venue_id,
        "source_ref": source_ref,
        "name": g("name"),
        "acronym": g("acronym"),
        "type": g("type") or "journal",
        "area": g("area"),
        "publisher_or_organizer": g("publisher_or_organizer"),
        "official_url": g("official_url"),
        "venue_family": _split_list(raw.get("venue_family", "")),
        "venue_family_labels": _family_labels(raw.get("venue_family", "")),
        "scope_summary": g("relevance_to_my_fields"),
        "quartile_or_rank": g("quartile_or_rank"),
        "ranking_source": g("ranking_source"),
        "indexing": g("indexing"),
        "q1_accessibility": {
            "class": g("q1_accessibility_class"),
            "rationale": g("accessibility_rationale"),
            "confidence": g("accessibility_confidence"),
        },
        "realistic_publication_chance": g("realistic_publication_chance"),
        "recommended_submission_strategy": g("recommended_submission_strategy"),
        "difficulty": g("difficulty"),
        "best_for": g("best_for"),
        "desk_reject_risks": g("desk_reject_risks"),
        "relevance_to_my_fields": g("relevance_to_my_fields"),
        "paper_profiles_supported": _split_list(raw.get("paper_profiles_supported", "")),
        "publication_timeline": {
            "time_to_first_decision": g("time_to_first_decision"),
            "time_to_acceptance": g("time_to_acceptance"),
            "time_acceptance_to_online": g("time_acceptance_to_online"),
            "estimated_total_publication_time": g("estimated_total_publication_time"),
            "publication_speed_category": g("publication_speed_category"),
            "expected_review_rounds": g("expected_review_rounds"),
            "fast_track_available": g("fast_track_available"),
            "online_first_available": g("online_first_available"),
            "timeline_confidence": g("timeline_confidence"),
            "timeline_source": g("timeline_source"),
        },
        "review_rigor": g("review_rigor"),
        "data_descriptor_format_available": g("data_descriptor_format_available"),
        "software_article_format_available": g("software_article_format_available"),
        "suitability_if_fast_publication_needed": g("suitability_if_fast_publication_needed"),
        "notes_on_publication_delay": g("notes_on_publication_delay"),
        "recent_related_papers": g("recent_related_papers"),
        "verification_links": g("verification_links"),
        "notes": g("notes"),
        "last_verified_at": "UNKNOWN",
        "imported_at": now_iso(),
        "import_source": source_name,
    }


def _write_venue_docs(profile: dict) -> Path:
    venue_id = profile["venue_id"]
    base = venues_dir() / "journals" / venue_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "recent_papers").mkdir(exist_ok=True)
    (base / "example_papers").mkdir(exist_ok=True)

    write_yaml(base / "venue_profile.yaml", profile)

    name = profile["name"]

    write_text(base / "overview.md", "\n".join([
        f"# {name} ({profile['acronym']})",
        "",
        f"- Type: {profile['type']}",
        f"- Publisher/organizer: {profile['publisher_or_organizer']}",
        f"- Official URL: {profile['official_url']}",
        f"- Venue families: {', '.join(profile['venue_family_labels']) or 'UNKNOWN'}",
        f"- Source: {profile['import_source']} (source_ref: {profile['source_ref']})",
        "",
        "## Scope summary",
        profile["scope_summary"],
        "",
        "## Best for",
        profile["best_for"],
    ]))

    write_text(base / "aims_and_scope.md", "\n".join([
        f"# Aims and scope — {name}", "",
        "NEEDS_USER_INPUT — upload the official aims & scope.", "",
        "## Relevance to my fields", profile["relevance_to_my_fields"],
    ]))

    write_text(base / "review_criteria.md", "\n".join([
        f"# Review criteria — {name}", "",
        "NEEDS_USER_INPUT — upload official review criteria.", "",
        f"- Review rigor: {profile['review_rigor']}",
        f"- Difficulty: {profile['difficulty']}",
        f"- Desk-reject risks: {profile['desk_reject_risks']}",
        f"- Paper profiles supported: {', '.join(profile['paper_profiles_supported']) or 'UNKNOWN'}",
    ]))

    write_text(base / "indexing_and_quartile.md", "\n".join([
        f"# Indexing and quartile — {name}", "",
        f"- Quartile / rank: {profile['quartile_or_rank']}",
        f"- Ranking source: {profile['ranking_source']}",
        f"- Indexing: {profile['indexing']}",
        "",
        "> Metrics are reproduced verbatim from the source. Unverified values are kept as-is; none are invented.",
        "",
        "## Verification links",
        profile["verification_links"],
    ]))

    tl = profile["publication_timeline"]
    write_text(base / "publication_timeline.md", "\n".join([
        f"# Publication timeline — {name}", "",
        f"- Time to first decision: {tl['time_to_first_decision']}",
        f"- Time to acceptance: {tl['time_to_acceptance']}",
        f"- Time acceptance to online: {tl['time_acceptance_to_online']}",
        f"- Estimated total publication time: {tl['estimated_total_publication_time']}",
        f"- Publication speed category: {tl['publication_speed_category']}",
        f"- Expected review rounds: {tl['expected_review_rounds']}",
        f"- Fast track available: {tl['fast_track_available']}",
        f"- Online first available: {tl['online_first_available']}",
        f"- Timeline confidence: {tl['timeline_confidence']}",
        f"- Timeline source: {tl['timeline_source']}",
        f"- Notes on delay: {profile['notes_on_publication_delay']}",
    ]))

    acc = profile["q1_accessibility"]
    write_text(base / "q1_accessibility.md", "\n".join([
        f"# Q1 accessibility — {name}", "",
        f"- Class: {acc['class']}",
        f"- Rationale: {acc['rationale']}",
        f"- Confidence: {acc['confidence']}",
        f"- Realistic publication chance: {profile['realistic_publication_chance']}",
        f"- Recommended submission strategy: {profile['recommended_submission_strategy']}",
    ]))

    write_text(base / "format_requirements.md",
               f"# Format requirements — {name}\n\nNEEDS_USER_INPUT — upload the venue template/format guide.\n")

    write_text(base / "verification_log.md", "\n".join([
        f"# Verification log — {name}", "",
        f"- {now_iso()} — imported from {profile['import_source']} (source_ref: {profile['source_ref']})",
        "- Quartiles/timelines reproduced verbatim; not independently verified.",
    ]))
    return base


# --------------------------------------------------------------------------- #
# Public import entry points
# --------------------------------------------------------------------------- #
def import_text(text: str, *, source_name: str, index_in_db: bool = True,
                used_ids: set[str] | None = None) -> ImportResult:
    fmt, raws = parse_source(text)
    result = ImportResult(source=source_name, detected_format=fmt)
    used = used_ids if used_ids is not None else _existing_venue_ids()

    for raw in raws:
        if not (raw.get("name") or raw.get("acronym")):
            result.skipped += 1
            continue
        original = (raw.get("venue_id") or "?").strip()
        venue_id, collision = stable_venue_id(raw, used)
        if collision:
            result.collisions_resolved += 1
        source_ref = f"{original} from {source_name}"
        profile = _build_profile(venue_id, source_ref, raw, source_name)
        base = _write_venue_docs(profile)
        rec = VenueRecord(venue_id=venue_id, source_ref=source_ref, raw=raw,
                          path_on_disk=str(base))
        result.venues.append(rec)
        if index_in_db:
            _upsert_venue_db(profile, base)

    _write_processed(result)
    _write_report(result)
    return result


def import_bytes(data: bytes, *, source_name: str, index_in_db: bool = True,
                 used_ids: set[str] | None = None) -> ImportResult:
    return import_text(smart_decode(data), source_name=source_name,
                       index_in_db=index_in_db, used_ids=used_ids)


def import_path(path: Path, *, index_in_db: bool = True) -> ImportResult:
    return import_bytes(Path(path).read_bytes(), source_name=Path(path).name, index_in_db=index_in_db)


def import_raw_dir(index_in_db: bool = True) -> list[ImportResult]:
    """Import every file in data/global_knowledge/venue_discovery/raw/."""
    raw_dir = global_knowledge_dir() / "venue_discovery" / "raw"
    results: list[ImportResult] = []
    used = _existing_venue_ids()
    for f in sorted(raw_dir.glob("*")):
        if f.is_file() and f.suffix.lower() in {".csv", ".md", ".txt", ".tsv"}:
            results.append(import_bytes(f.read_bytes(), source_name=f.name,
                                        index_in_db=index_in_db, used_ids=used))
    return results


# --------------------------------------------------------------------------- #
# Outputs + DB
# --------------------------------------------------------------------------- #
def _existing_venue_ids() -> set[str]:
    journals = venues_dir() / "journals"
    if not journals.exists():
        return set()
    return {p.name for p in journals.iterdir() if p.is_dir()}


def _write_processed(result: ImportResult) -> None:
    proc_dir = global_knowledge_dir() / "venue_discovery" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    columns = ["venue_id", "source_ref"] + _columns()
    rows = []
    for rec in result.venues:
        row = {"venue_id": rec.venue_id, "source_ref": rec.source_ref}
        row.update(rec.raw)
        rows.append(row)

    json_path = proc_dir / "venues_normalized.json"
    # Merge with any prior normalized data so multiple imports accumulate.
    existing = []
    if json_path.exists():
        import json
        try:
            existing = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    by_id = {r["venue_id"]: r for r in existing if isinstance(r, dict) and "venue_id" in r}
    for r in rows:
        by_id[r["venue_id"]] = r
    merged = list(by_id.values())
    write_json(json_path, merged)
    result.processed_json = str(json_path)

    csv_path = proc_dir / "venues_normalized.csv"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in merged:
        writer.writerow(r)
    write_text(csv_path, buf.getvalue())
    result.processed_csv = str(csv_path)


def _write_report(result: ImportResult) -> None:
    rep_dir = global_knowledge_dir() / "venue_discovery" / "import_reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = rep_dir / f"{ts}_import_report.md"

    unverified = 0
    for rec in result.venues:
        for v in rec.raw.values():
            if isinstance(v, str) and "not verified" in v.lower():
                unverified += 1

    lines = [
        f"# Venue discovery import report — {result.source}",
        "",
        f"- Imported at: {now_iso()}",
        f"- Detected format: {result.detected_format}",
        f"- Venues imported: {len(result.venues)}",
        f"- Rows skipped (no name/acronym): {result.skipped}",
        f"- ID collisions resolved (slug suffix): {result.collisions_resolved}",
        f"- 'not verified' field occurrences preserved: {unverified}",
        "",
        "## Imported venues",
        "",
        "| venue_id | source_ref | name |",
        "| --- | --- | --- |",
    ]
    for rec in result.venues:
        lines.append(f"| {rec.venue_id} | {rec.source_ref} | {rec.raw.get('name','')} |")
    if result.warnings:
        lines += ["", "## Warnings"] + [f"- {w}" for w in result.warnings]
    write_text(path, "\n".join(lines) + "\n")
    result.report_path = str(path)


def _upsert_venue_db(profile: dict, base: Path) -> None:
    try:
        from sqlalchemy import select

        from worker.db import Venue, VenueFile, session_scope

        with session_scope() as s:
            venue = s.scalar(select(Venue).where(Venue.venue_id == profile["venue_id"]))
            if venue is None:
                venue = Venue(venue_id=profile["venue_id"])
                s.add(venue)
            venue.name = profile["name"]
            venue.acronym = profile["acronym"]
            venue.type = profile["type"]
            venue.venue_family = ", ".join(profile["venue_family_labels"]) or "UNKNOWN"
            venue.quartile_or_rank = profile["quartile_or_rank"]
            venue.q1_accessibility_class = profile["q1_accessibility"]["class"]
            venue.publication_speed_category = profile["publication_timeline"]["publication_speed_category"]
            venue.review_rigor = profile["review_rigor"]
            venue.official_url = profile["official_url"]
            venue.path_on_disk = str(base)
            venue.source_ref = profile["source_ref"]
            venue.last_verified_at = profile["last_verified_at"]
            # Index the venue files.
            existing_files = {
                f.path_on_disk for f in s.scalars(
                    select(VenueFile).where(VenueFile.venue_id == profile["venue_id"])
                )
            }
            for md in sorted(base.glob("*.md")) + [base / "venue_profile.yaml"]:
                if str(md) not in existing_files:
                    s.add(VenueFile(venue_id=profile["venue_id"], file_kind=md.name, path_on_disk=str(md)))
    except Exception:
        # DB indexing is best-effort; the Markdown is the source of truth.
        pass
