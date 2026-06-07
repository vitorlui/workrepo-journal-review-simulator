#!/usr/bin/env python3
"""Export the final review package (zip + best-effort PDF).

    python scripts/export_review_package.py --review-id <review_id>
"""
from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.exporters import export_review_package


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the final review package.")
    parser.add_argument("--review-id", required=True)
    args = parser.parse_args()
    init_db(seed=True)
    info = export_review_package(args.review_id)
    print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
