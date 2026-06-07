#!/usr/bin/env python3
"""Regenerate db/schema.sql from the canonical SQLAlchemy models (plan C9).

Usage:  python scripts/dump_schema.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.schema import CreateTable  # noqa: E402

from worker.db import Base  # noqa: E402

HEADER = (
    "-- Generated reference snapshot of the SQLAlchemy models in worker/db.py (plan C9).\n"
    "-- The ORM models are canonical; regenerate with scripts/dump_schema.py.\n"
    "-- The DB is an INDEX + workflow-state manager only; Markdown/YAML is the source of truth.\n\n\n"
)


def main() -> None:
    parts = [HEADER]
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()
        ddl = ddl.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1)
        parts.append(ddl + ";\n")
    out = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    out.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(f"Wrote {out} ({len(Base.metadata.sorted_tables)} tables).")


if __name__ == "__main__":
    main()
