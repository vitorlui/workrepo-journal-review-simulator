#!/usr/bin/env python3
"""Run a single Execute-query against an engine CLI, no frontend needed.

    python scripts/run_query.py --review-id <id> --venue <venue_id> \\
        --reviewer reviewer-methodology --engine claude

Engines: claude | codex | ollama | gemini (must be installed + logged in).
Use --status to list which CLIs are detected.
"""
from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.engines import engine_status, query_engines
from worker.run_query import execute_query


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a prompt through an engine CLI.")
    parser.add_argument("--status", action="store_true", help="List engine availability and exit.")
    parser.add_argument("--review-id")
    parser.add_argument("--venue", default="")
    parser.add_argument("--reviewer", default="reviewer-methodology")
    parser.add_argument("--engine", default="claude", choices=query_engines())
    args = parser.parse_args()

    init_db(seed=True)

    if args.status:
        print(json.dumps(engine_status(), indent=2, ensure_ascii=False))
        return

    if not args.review_id:
        parser.error("--review-id is required (or use --status)")

    out = execute_query(args.review_id, args.venue, args.reviewer, args.engine)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
