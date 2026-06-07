"""FastAPI app factory.

Thin HTTP layer over the worker/ core library (plan C6). On startup it ensures
the documental directories exist, creates/seeds the DB and indexes any venues
already present on disk.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the repo root importable so `import worker.*` works in all contexts (C6).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.core import settings  # noqa: E402
from app.routers import (  # noqa: E402
    catalog,
    export,
    pipeline,
    responses,
    reviews,
    venue_discovery,
    venues,
)
from worker.db import init_db  # noqa: E402
from worker.paths import ensure_base_dirs  # noqa: E402
from worker.venues import scan_venue_markdowns  # noqa: E402

@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_base_dirs()
    init_db(seed=True)
    try:
        scan_venue_markdowns(index_in_db=True)
    except Exception:
        pass
    yield


app = FastAPI(
    title="journal-review-simulator API",
    version="0.1.0",
    description="Pre-submission editorial review simulator. Markdown is the semantic memory; the DB is an index.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "journal-review-simulator-api"}


app.include_router(reviews.router)
app.include_router(pipeline.router)
app.include_router(venues.router)
app.include_router(venue_discovery.router)
app.include_router(responses.router)
app.include_router(catalog.router)
app.include_router(export.router)
