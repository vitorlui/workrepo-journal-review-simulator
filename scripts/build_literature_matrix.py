#!/usr/bin/env python3
"""Create the literature-query template + empty literature matrix for a review.

    python scripts/build_literature_matrix.py --review-id <review_id>

Does NOT invent references. Generates queries + an empty matrix for the user to
fill with real results pasted from Perplexity/Scholar/Semantic Scholar.
"""
from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.pipeline_runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build literature query template + matrix.")
    parser.add_argument("--review-id", required=True)
    args = parser.parse_args()
    init_db(seed=True)
    result = run_pipeline(args.review_id, "literature_queries")
    print("Outputs:", result.outputs)


if __name__ == "__main__":
    main()
