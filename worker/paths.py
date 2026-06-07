"""Path and configuration resolution for the whole project.

All filesystem access goes through ``pathlib`` (plan deviation B5) and is
anchored on the repository root so the same code works from the FastAPI
container, the worker container and native ``scripts/`` runs on Windows.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path

import yaml

# worker/paths.py -> worker/ -> <repo root>
REPO_ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = REPO_ROOT / "config"
PROMPTS_DIR = REPO_ROOT / "prompts"


def data_dir() -> Path:
    """Root of the documental memory.

    Honours the ``DATA_DIR`` env var (set in Docker to ``/app/data``) and
    falls back to ``<repo>/data`` for native runs.
    """
    env = os.environ.get("DATA_DIR")
    base = Path(env) if env else (REPO_ROOT / "data")
    return base


def global_knowledge_dir() -> Path:
    return data_dir() / "global_knowledge"


def venues_dir() -> Path:
    return global_knowledge_dir() / "venues"


def reviews_dir() -> Path:
    return data_dir() / "reviews"


def uploads_dir() -> Path:
    return data_dir() / "uploads"


def review_dir(review_id: str) -> Path:
    return reviews_dir() / review_id


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_base_dirs() -> None:
    """Create the top-level documental directories if missing."""
    for sub in (
        venues_dir() / "journals",
        venues_dir() / "conferences",
        venues_dir() / "template",
        global_knowledge_dir() / "venue_discovery" / "raw",
        global_knowledge_dir() / "venue_discovery" / "processed",
        global_knowledge_dir() / "venue_discovery" / "import_reports",
        global_knowledge_dir() / "recent_papers",
        global_knowledge_dir() / "literature",
        global_knowledge_dir() / "reviewer_profiles",
        global_knowledge_dir() / "prompt_templates",
        reviews_dir(),
        uploads_dir() / "quarantine",
    ):
        ensure_dir(sub)


@functools.lru_cache(maxsize=None)
def load_config(name: str) -> dict:
    """Load and cache ``config/<name>.yaml`` as a dict."""
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
