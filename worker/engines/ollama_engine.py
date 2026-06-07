"""Local models via the Ollama HTTP API."""
from __future__ import annotations

import os
from typing import Optional

from worker.engines.base import EngineResult, ReviewEngine, http_post_json


class OllamaEngine(ReviewEngine):
    name = "ollama"

    def host(self) -> str:
        return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    def model(self) -> str:
        return os.environ.get("OLLAMA_MODEL", "llama3.1")

    def available(self) -> bool:
        # Ollama needs no API key; treat as available if a host is configured.
        return bool(self.host())

    def complete(self, prompt: str, *, system: Optional[str] = None) -> EngineResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model(), "messages": messages, "stream": False}
        try:
            data = http_post_json(f"{self.host()}/api/chat", payload)
            text = (data.get("message") or {}).get("content", "")
            return EngineResult(True, text, self.name, self.model())
        except Exception as exc:  # noqa: BLE001
            return EngineResult(False, "", self.name, self.model(), error=str(exc))
