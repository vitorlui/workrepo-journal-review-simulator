"""Export endpoints: build the package and download the zip."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from worker import reviews as review_svc
from worker.exporters import export_review_package
from worker.paths import review_dir

router = APIRouter(prefix="/reviews", tags=["export"])


@router.post("/{review_id}/export")
def build_export(review_id: str) -> dict:
    if review_svc.get_review(review_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return export_review_package(review_id)


@router.get("/{review_id}/export/download")
def download_export(review_id: str):
    zip_path = review_dir(review_id) / "exports" / "full_review_package.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="No export yet. Build it first.")
    return FileResponse(str(zip_path), media_type="application/zip", filename=zip_path.name)
