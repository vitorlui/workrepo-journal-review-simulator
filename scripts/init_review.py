#!/usr/bin/env python3
"""Create a new review (unique ID + documental tree + DB row).

    python scripts/init_review.py --title "My paper" --submission-type new_submission
"""
from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.reviews import create_review


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise a new review.")
    parser.add_argument("--title", default="UNKNOWN")
    parser.add_argument("--submission-type", default="new_submission")
    args = parser.parse_args()

    init_db(seed=True)
    info = create_review(title=args.title, submission_type=args.submission_type)
    print(info.review_id)
    print(info.path_on_disk)


if __name__ == "__main__":
    main()
