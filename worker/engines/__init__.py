"""LLM engine layer.

Primary path (per user flow): run the local **CLI** of each tool
(Codex/ChatGPT, Claude Code, Ollama, Gemini) with our generated prompt and
capture stdout. No browser automation, no API keys. Command templates live in
``config/model_config.yaml`` under ``cli_engines``.

Optional HTTP API adapters (``ollama_engine``, ``openai_engine``) are available
for setups that prefer APIs, but the default registry is CLI-based.

Everything is offline-safe: if a CLI is not installed, the engine reports
``available() == False`` and callers fall back to the offline ``template``
scaffold.
"""
from __future__ import annotations

import functools

from worker.engines.base import EngineResult, ReviewEngine
from worker.engines.cli_engine import CliEngine
from worker.paths import load_config


@functools.lru_cache(maxsize=1)
def _registry() -> dict[str, CliEngine]:
    specs = load_config("model_config").get("cli_engines", {}) or {}
    return {name: CliEngine(name, spec) for name, spec in specs.items()}


def get_engine(name: str) -> CliEngine | None:
    return _registry().get((name or "").lower())


def query_engines() -> list[str]:
    """Engines offered by the Execute-query UI, in configured order."""
    return load_config("model_config").get("query_engines", list(_registry().keys()))


def engine_status() -> dict[str, dict]:
    """Availability + resolved model/binary for each configured engine."""
    out: dict[str, dict] = {}
    for name, eng in _registry().items():
        out[name] = {
            "available": eng.available(),
            "bin": eng._bin,
            "resolved": eng.resolved_bin(),
            "model": eng.model(),
        }
    return out


def run_query(engine: str, prompt: str, *, system: str | None = None) -> EngineResult:
    """Run a prompt through an engine's CLI and return the result."""
    eng = get_engine(engine)
    if eng is None:
        return EngineResult(False, "", engine, engine, error=f"Unknown engine '{engine}'")
    return eng.complete(prompt, system=system)


__all__ = [
    "EngineResult",
    "ReviewEngine",
    "CliEngine",
    "get_engine",
    "query_engines",
    "engine_status",
    "run_query",
]
