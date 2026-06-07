"""Venue indexing, candidate discovery and fit/timeline reports.

Reads the venue documental memory (``venue_profile.yaml`` files), indexes them
in the DB, and ranks candidate venues for a review by family/keyword overlap.
Never invents venues or metrics.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from worker.markdown_store import now_iso, read_yaml, write_text
from worker.paths import review_dir, venues_dir


@dataclass
class VenueSummary:
    venue_id: str
    name: str
    acronym: str
    type: str
    families: list[str]
    family_labels: list[str]
    q1_accessibility_class: str
    quartile_or_rank: str
    publication_speed_category: str
    review_rigor: str
    path_on_disk: str


def _iter_venue_dirs():
    for kind in ("journals", "conferences"):
        base = venues_dir() / kind
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and (d / "venue_profile.yaml").exists():
                yield d


def list_venues() -> list[VenueSummary]:
    out: list[VenueSummary] = []
    for d in _iter_venue_dirs():
        p = read_yaml(d / "venue_profile.yaml")
        tl = p.get("publication_timeline", {}) or {}
        out.append(VenueSummary(
            venue_id=p.get("venue_id", d.name),
            name=p.get("name", "UNKNOWN"),
            acronym=p.get("acronym", "UNKNOWN"),
            type=p.get("type", "journal"),
            families=[str(x) for x in (p.get("venue_family") or [])],
            family_labels=p.get("venue_family_labels", []) or [],
            q1_accessibility_class=p.get("q1_accessibility", {}).get("class", "UNKNOWN")
            if isinstance(p.get("q1_accessibility"), dict) else "UNKNOWN",
            quartile_or_rank=p.get("quartile_or_rank", "UNKNOWN"),
            publication_speed_category=tl.get("publication_speed_category", "UNKNOWN"),
            review_rigor=p.get("review_rigor", "UNKNOWN"),
            path_on_disk=str(d),
        ))
    return out


def scan_venue_markdowns(index_in_db: bool = True) -> int:
    """Re-index every venue_profile.yaml into the DB. Returns count."""
    venues = list_venues()
    if index_in_db:
        try:
            from sqlalchemy import select

            from worker.db import Venue, session_scope
            with session_scope() as s:
                for v in venues:
                    row = s.scalar(select(Venue).where(Venue.venue_id == v.venue_id))
                    if row is None:
                        row = Venue(venue_id=v.venue_id)
                        s.add(row)
                    row.name = v.name
                    row.acronym = v.acronym
                    row.type = v.type
                    row.venue_family = ", ".join(v.family_labels) or "UNKNOWN"
                    row.quartile_or_rank = v.quartile_or_rank
                    row.q1_accessibility_class = v.q1_accessibility_class
                    row.publication_speed_category = v.publication_speed_category
                    row.review_rigor = v.review_rigor
                    row.path_on_disk = v.path_on_disk
        except Exception:
            pass
    return len(venues)


def discover_venues(review_id: str, likely_families: list[int] | None = None) -> list[dict]:
    """Rank existing venues by overlap with the review's detected families."""
    likely = {str(f) for f in (likely_families or [])}
    ranked = []
    for v in list_venues():
        overlap = len(set(v.families) & likely)
        ranked.append({
            "venue_id": v.venue_id,
            "name": v.name,
            "acronym": v.acronym,
            "type": v.type,
            "score": overlap,
            "family_labels": v.family_labels,
            "q1_accessibility_class": v.q1_accessibility_class,
            "quartile_or_rank": v.quartile_or_rank,
            "publication_speed_category": v.publication_speed_category,
            "review_rigor": v.review_rigor,
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def write_venue_fit_report(review_id: str, venue_ids: list[str]) -> Path:
    lines = [f"# Venue fit report — {review_id}", "", f"_Generated {now_iso()} — PROVISIONAL (venue data may be incomplete)._", ""]
    for vid in venue_ids:
        base = venues_dir() / "journals" / vid
        p = read_yaml(base / "venue_profile.yaml") if base.exists() else {}
        acc = p.get("q1_accessibility", {}) if isinstance(p.get("q1_accessibility"), dict) else {}
        lines += [
            f"## {p.get('name', vid)} ({vid})",
            f"- Quartile / rank: {p.get('quartile_or_rank', 'UNKNOWN')}",
            f"- Q1 accessibility: {acc.get('class', 'UNKNOWN')}",
            f"- Review rigor: {p.get('review_rigor', 'UNKNOWN')}",
            f"- Desk-reject risks: {p.get('desk_reject_risks', 'UNKNOWN')}",
            f"- Scientific fit: NEEDS_USER_INPUT (provisional)",
            f"- Recommended strategy: {p.get('recommended_submission_strategy', 'UNKNOWN')}",
            "",
        ]
    path = review_dir(review_id) / "venues" / "venue_fit_report.md"
    write_text(path, "\n".join(lines))
    return path


def write_timeline_report(review_id: str, venue_ids: list[str]) -> Path:
    lines = [f"# Venue timeline report — {review_id}", "", f"_Generated {now_iso()}_", ""]
    for vid in venue_ids:
        base = venues_dir() / "journals" / vid
        p = read_yaml(base / "venue_profile.yaml") if base.exists() else {}
        tl = p.get("publication_timeline", {}) or {}
        lines += [
            f"## {p.get('name', vid)} ({vid})",
            f"- Time to first decision: {tl.get('time_to_first_decision', 'UNKNOWN')}",
            f"- Time to acceptance: {tl.get('time_to_acceptance', 'UNKNOWN')}",
            f"- Estimated total publication time: {tl.get('estimated_total_publication_time', 'UNKNOWN')}",
            f"- Publication speed: {tl.get('publication_speed_category', 'UNKNOWN')}",
            f"- Timeline confidence: {tl.get('timeline_confidence', 'UNKNOWN')}",
            f"- Timeline source: {tl.get('timeline_source', 'UNKNOWN')}",
            "",
        ]
    path = review_dir(review_id) / "venues" / "venue_timeline_report.md"
    write_text(path, "\n".join(lines))
    return path


def write_desk_reject_precheck(review_id: str) -> Path:
    checks = [
        "Is the paper clearly out of scope?",
        "Is there a clear contribution?",
        "Is there minimal experimental evaluation?",
        "Is the format far from the venue's requirements?",
        "Are references incomplete?",
        "Are there claims without evidence?",
        "Does the venue require data/code the paper does not declare?",
        "Are there obvious ethical problems?",
        "Does the paper seem not ready for review?",
    ]
    rows = "\n".join(f"| {c} | NEEDS_USER_INPUT |" for c in checks)
    body = (
        f"# Desk-reject precheck — {review_id}\n\n"
        f"_Generated {now_iso()} — this is a warning, it does not stop the pipeline._\n\n"
        "| Check | Finding |\n| --- | --- |\n" + rows + "\n"
    )
    path = review_dir(review_id) / "venues" / "desk_reject_precheck.md"
    write_text(path, body)
    return path
