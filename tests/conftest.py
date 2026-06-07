"""Pytest configuration.

Isolates every test run in a temporary DATA_DIR (so tests never touch the real
documental memory) and uses the SQLite fallback. Must set env vars before any
worker import so the DB engine and paths resolve to the temp location.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Isolate data + DB before importing worker.*
_TMP = Path(tempfile.mkdtemp(prefix="jrs_test_"))
os.environ["DATA_DIR"] = str(_TMP)
os.environ.pop("DATABASE_URL", None)  # -> sqlite fallback inside _TMP
os.environ["PIPELINE_ENGINE"] = "template"

import pytest  # noqa: E402

from worker.db import init_db  # noqa: E402
from worker.paths import ensure_base_dirs  # noqa: E402

SAMPLE_PAPER = REPO_ROOT / "tests" / "sample_paper" / "manuscript.md"
VENUE_FILE_1 = REPO_ROOT / "docs" / "init_plan" / "perplexity_database_responses" / "final_response1.csv"
VENUE_FILE_2 = REPO_ROOT / "docs" / "init_plan" / "perplexity_database_responses" / "final_response2.csv"


@pytest.fixture(scope="session", autouse=True)
def _bootstrap():
    ensure_base_dirs()
    init_db(seed=True)
    yield


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
