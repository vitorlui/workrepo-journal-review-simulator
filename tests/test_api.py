"""API smoke tests via FastAPI TestClient."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# The API app lives under apps/api; add it to the path for `import app.main`.
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_create_and_get_review(client):
    r = client.post("/reviews", json={"title": "api test", "submission_type": "new_submission"})
    assert r.status_code == 200
    rid = r.json()["review_id"]
    assert rid.startswith("REV-")
    got = client.get(f"/reviews/{rid}")
    assert got.status_code == 200
    assert got.json()["title"] == "api test"


def test_pipeline_modes_listed(client):
    modes = client.get("/pipeline/modes").json()["modes"]
    assert "full_review" in modes and "extract" in modes


def test_reviewer_profiles_and_engines(client):
    rp = client.get("/reviewer-profiles").json()
    assert len(rp["main_reviewers"]) == 5
    eng = client.get("/ai-engines").json()
    assert eng["default_engine"] == "template"


def test_run_pipeline_init(client):
    rid = client.post("/reviews", json={"title": "run", "submission_type": "new_submission"}).json()["review_id"]
    res = client.post(f"/pipeline/{rid}/run", params={"mode": "init"})
    assert res.status_code == 200
    assert res.json()["mode"] == "init"
