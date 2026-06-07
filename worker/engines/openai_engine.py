"""ChatGPT-class models via the OpenAI-compatible Chat Completions API.

Works with OpenAI and any OpenAI-compatible endpoint (set OPENAI_BASE_URL).
"""
from __future__ import annotations

import os
from typing import Optional

from worker.engines.base import EngineResult, ReviewEngine, http_post_json


class OpenAIEngine(ReviewEngine):
    name = "openai"

    def base_url(self) -> str:
        return os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    def model(self) -> str:
        return os.environ.get("OPENAI_MODEL", "gpt-4o")

    def _key(self) -> str:
        return os.environ.get("OPENAI_API_KEY", "")

    def available(self) -> bool:
        return bool(self._key())

    def complete(self, prompt: str, *, system: Optional[str] = None) -> EngineResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model(), "messages": messages, "temperature": 0.2}
        headers = {"Authorization": f"Bearer {self._key()}"}
        try:
            data = http_post_json(f"{self.base_url()}/chat/completions", payload, headers=headers)
            text = data["choices"][0]["message"]["content"]
            return EngineResult(True, text, self.name, self.model())
        except Exception as exc:  # noqa: BLE001
            return EngineResult(False, "", self.name, self.model(), error=str(exc))
