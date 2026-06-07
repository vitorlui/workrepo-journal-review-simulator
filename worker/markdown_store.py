"""Helpers for the Markdown/YAML semantic memory.

Pure filesystem utilities: slugging, atomic-ish writes, YAML round-tripping and
simple front-matter handling. No DB access here.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def slugify(value: str, *, max_len: int = 80) -> str:
    """Filesystem-safe slug (ascii, lowercase, hyphen-separated)."""
    value = str(value or "").strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        value = "item"
    return value[:max_len].strip("-")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def read_yaml(path: Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def write_json(path: Path, data: Any) -> Path:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line.rstrip("\n") + "\n")


def kv_block(data: dict) -> str:
    """Render a dict as a Markdown bullet list of ``- key: value`` lines."""
    lines = []
    for key, value in data.items():
        lines.append(f"- **{key}:** {value}")
    return "\n".join(lines)
