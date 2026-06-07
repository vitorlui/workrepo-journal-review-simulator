#!/usr/bin/env python3
"""Main pipeline CLI.

    python scripts/run_pipeline.py --review-id <review_id> --mode full_review

Supported modes are listed in worker.pipeline_runner.MODES.
"""
from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401  (sets sys.path)

from worker.db import init_db
from worker.pipeline_runner import MODES, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a review pipeline mode.")
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--mode", default="full_review", choices=MODES)
    args = parser.parse_args()

    init_db(seed=True)
    result = run_pipeline(args.review_id, args.mode)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
