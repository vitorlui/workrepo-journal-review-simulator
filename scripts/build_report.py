#!/usr/bin/env python3
"""Assemble the editor decision package for a review (editorial_decision mode).

    python scripts/build_report.py --review-id <review_id>
"""
from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.pipeline_runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the editor decision package.")
    parser.add_argument("--review-id", required=True)
    args = parser.parse_args()
    init_db(seed=True)
    result = run_pipeline(args.review_id, "editorial_decision")
    print("Outputs:", result.outputs)


if __name__ == "__main__":
    main()
