#!/usr/bin/env python3
"""Re-index all venue_profile.yaml files into the DB.

    python scripts/scan_venue_markdowns.py
"""
from __future__ import annotations

import _bootstrap  # noqa: F401

from worker.db import init_db
from worker.venues import scan_venue_markdowns


def main() -> None:
    init_db(seed=True)
    n = scan_venue_markdowns(index_in_db=True)
    print(f"Indexed {n} venues from the documental memory.")


if __name__ == "__main__":
    main()
