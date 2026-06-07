#!/usr/bin/env python3
"""Validate that the expected project structure and key files exist.

    python scripts/check_structure.py
"""
from __future__ import annotations

import sys

import _bootstrap  # noqa: F401

from worker.paths import REPO_ROOT

REQUIRED = [
    # Top-level
    "README.md", "docker-compose.yml", ".env.example", ".gitignore", ".gitattributes",
    "CLAUDE.md",
    # Config
    "config/pipeline.yaml", "config/scoring_rubrics.yaml", "config/model_config.yaml",
    "config/reviewer_profiles.yaml", "config/venue_discovery.yaml",
    "config/external_engines.yaml", "config/upload_policy.yaml",
    # DB
    "db/schema.sql", "db/seed/external_engines.sql", "db/seed/reviewer_profiles.sql",
    # Worker
    "worker/__init__.py", "worker/review_id.py", "worker/file_ingestion.py",
    "worker/extraction.py", "worker/classify.py", "worker/markdown_store.py",
    "worker/external_prompt_manager.py", "worker/agent_orchestrator.py",
    "worker/pipeline_runner.py", "worker/exporters.py", "worker/venue_discovery.py",
    "worker/venues.py", "worker/reviews.py", "worker/external_responses.py", "worker/db.py",
    # API
    "apps/api/app/main.py", "apps/api/requirements.txt", "apps/api/pyproject.toml",
    "apps/api/app/routers/reviews.py", "apps/api/app/routers/venue_discovery.py",
    # Web
    "apps/web/package.json", "apps/web/app/layout.tsx", "apps/web/app/page.tsx",
    # Scripts
    "scripts/run_pipeline.py", "scripts/init_review.py", "scripts/parse_paper.py",
    "scripts/discover_venues.py", "scripts/scan_venue_markdowns.py",
    "scripts/import_venue_discovery.py", "scripts/build_literature_matrix.py",
    "scripts/compare_models.py", "scripts/build_report.py", "scripts/export_review_package.py",
    # Agents / skills / profiles
    ".claude/agents/editor-in-chief.md",
    ".claude/agents/reviewer-methodology.md",
    ".claude/skills/review-paper-reviewer/SKILL.md",
    "data/global_knowledge/reviewer_profiles/reviewer-methodology.md",
    # Venue discovery folders
    "data/global_knowledge/venue_discovery/raw",
    "data/global_knowledge/venue_discovery/processed",
    "data/global_knowledge/venue_discovery/import_reports",
    "data/global_knowledge/venues/template",
]


def main() -> int:
    missing = []
    for rel in REQUIRED:
        if not (REPO_ROOT / rel).exists():
            missing.append(rel)
    total = len(REQUIRED)
    ok = total - len(missing)
    print(f"Structure check: {ok}/{total} present.")
    if missing:
        print("\nMISSING:")
        for m in missing:
            print(f"  - {m}")
        return 1
    print("All required paths present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
