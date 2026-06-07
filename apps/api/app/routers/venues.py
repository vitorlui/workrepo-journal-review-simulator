"""Venues: list, get, create (manual), import CSV/Markdown."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from worker import venue_discovery as vd
from worker import venues as venue_mod
from worker.markdown_store import read_yaml
from worker.paths import venues_dir

router = APIRouter(prefix="/venues", tags=["venues"])


class CreateVenueIn(BaseModel):
    name: str
    acronym: str = "UNKNOWN"
    type: str = "journal"
    official_url: str = "UNKNOWN"
    venue_family: list[str] = []
    area: str = "UNKNOWN"


def _summary_dict(v: venue_mod.VenueSummary) -> dict:
    return {
        "venue_id": v.venue_id,
        "name": v.name,
        "acronym": v.acronym,
        "type": v.type,
        "family_labels": v.family_labels,
        "q1_accessibility_class": v.q1_accessibility_class,
        "quartile_or_rank": v.quartile_or_rank,
        "publication_speed_category": v.publication_speed_category,
        "review_rigor": v.review_rigor,
    }


@router.get("")
def list_venues() -> list[dict]:
    return [_summary_dict(v) for v in venue_mod.list_venues()]


@router.get("/{venue_id}")
def get_venue(venue_id: str) -> dict:
    base = venues_dir() / "journals" / venue_id
    if not base.exists():
        base = venues_dir() / "conferences" / venue_id
    profile = read_yaml(base / "venue_profile.yaml") if base.exists() else None
    if not profile:
        raise HTTPException(status_code=404, detail="Venue not found")
    docs = {p.stem: p.read_text(encoding="utf-8") for p in base.glob("*.md")}
    return {"profile": profile, "docs": docs}


@router.post("")
def create_venue(body: CreateVenueIn) -> dict:
    # Build a minimal raw record and reuse the importer's doc generation.
    raw = {
        "venue_id": "MANUAL",
        "name": body.name,
        "acronym": body.acronym,
        "type": body.type,
        "area": body.area,
        "official_url": body.official_url,
        "venue_family": ",".join(body.venue_family),
    }
    used = {p.name for p in (venues_dir() / "journals").glob("*") if p.is_dir()}
    venue_id, _ = vd.stable_venue_id(raw, used)
    profile = vd._build_profile(venue_id, "manual entry", raw, "manual")
    base = vd._write_venue_docs(profile)
    vd._upsert_venue_db(profile, base)
    return {"venue_id": venue_id, "path_on_disk": str(base)}


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)) -> dict:
    """Import a venue CSV / Markdown-table (same engine as venue-discovery)."""
    data = await file.read()
    result = vd.import_bytes(data, source_name=file.filename or "upload.csv", index_in_db=True)
    return {
        "detected_format": result.detected_format,
        "imported": len(result.venues),
        "skipped": result.skipped,
        "collisions_resolved": result.collisions_resolved,
        "report_path": result.report_path,
    }
