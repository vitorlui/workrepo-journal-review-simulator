#!/usr/bin/env python3
"""Import Perplexity venue responses (Markdown pipe-table or CSV).

Import everything currently in data/global_knowledge/venue_discovery/raw/:
    python scripts/import_venue_discovery.py

Import a specific file:
    python scripts/import_venue_discovery.py --file path/to/response.csv

Future Perplexity responses: drop them into the raw/ folder (or pass --file)
and re-run. Stable venue IDs prevent collisions from overwriting venues.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.paths import ensure_base_dirs
from worker.venue_discovery import import_path, import_raw_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Import venue discovery responses.")
    parser.add_argument("--file", help="Import a single file instead of the whole raw/ dir.")
    parser.add_argument("--no-db", action="store_true", help="Skip DB indexing.")
    args = parser.parse_args()

    ensure_base_dirs()
    init_db(seed=True)
    index = not args.no_db

    if args.file:
        results = [import_path(Path(args.file), index_in_db=index)]
    else:
        results = import_raw_dir(index_in_db=index)

    if not results:
        print("No venue files found. Drop .csv/.md files into "
              "data/global_knowledge/venue_discovery/raw/ or pass --file.")
        return

    total = 0
    for r in results:
        total += len(r.venues)
        print(f"{r.source}: format={r.detected_format} imported={len(r.venues)} "
              f"skipped={r.skipped} collisions_resolved={r.collisions_resolved}")
        print(f"  report: {r.report_path}")
    print(f"TOTAL venues imported: {total}")


if __name__ == "__main__":
    main()
