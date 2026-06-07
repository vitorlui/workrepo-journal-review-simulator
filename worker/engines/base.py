"""Engine interface + shared HTTP helper (stdlib only, no extra deps)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class EngineResult:
    ok: bool
    text: str
    engine: str
    model: str
    error: Optional[str] = None


class ReviewEngine:
    """Base adapter. Subclasses set ``name`` and implement ``complete``."""

    name: str = "base"

    def available(self) -> bool:  # pragma: no cover - trivial
        return False

    def model(self) -> str:  # pragma: no cover - trivial
        return self.name

    def complete(self, prompt: str, *, system: Optional[str] = None) -> EngineResult:
        raise NotImplementedError


def http_post_json(
    url: str,
    payload: dict,
    *,
    headers: Optional[dict] = None,
    timeout: int = 120,
) -> dict:
    """POST JSON and return parsed JSON. Raises urllib errors on failure.

    Isolated here so tests can monkeypatch a single function.
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))
