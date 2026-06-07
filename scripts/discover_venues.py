#!/usr/bin/env python3
"""Rank candidate venues for a review by detected-area overlap.

    python scripts/discover_venues.py --review-id <review_id>
"""
from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.markdown_store import read_yaml
from worker.paths import review_dir
from worker.venues import discover_venues


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover candidate venues.")
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    init_db(seed=True)
    meta = read_yaml(review_dir(args.review_id) / "metadata.yaml")
    ranked = discover_venues(args.review_id, meta.get("likely_venue_families", []))
    print(json.dumps(ranked[: args.top], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
