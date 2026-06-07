"""Generic CLI engine runner.

Executes a local LLM CLI (Codex/ChatGPT, Claude Code, Ollama, Gemini) with our
generated prompt and captures stdout as the review. No browser automation, no
API keys — it reuses the CLIs the user already has installed.

Command templates are configurable in config/model_config.yaml under
``cli_engines`` so flags can be adjusted without code changes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Optional

from worker.engines.base import EngineResult, ReviewEngine

try:  # optional safety net for mojibake / mixed encodings
    import ftfy

    def _fix_text(s: str) -> str:
        return ftfy.fix_text(s or "")
except Exception:  # pragma: no cover
    def _fix_text(s: str) -> str:
        return s or ""


class CliEngine(ReviewEngine):
    def __init__(self, name: str, spec: dict):
        self.name = name
        self.spec = spec or {}
        self._bin = self.spec.get("bin", name)
        self._cmd: list[str] = list(self.spec.get("cmd", [self._bin]))
        self._pass_via = self.spec.get("pass_via", "stdin")  # "stdin" | "arg"
        self._timeout = int(self.spec.get("timeout", 300))

    # -- model substitution -------------------------------------------------
    def model(self) -> str:
        import os
        env = self.spec.get("model_env")
        if env and os.environ.get(env):
            return os.environ[env]
        return self.spec.get("default_model", self.name)

    def resolved_bin(self) -> Optional[str]:
        return shutil.which(self._bin)

    def available(self) -> bool:
        return self.resolved_bin() is not None

    def _argv(self) -> list[str]:
        argv = [a.replace("{model}", self.model()) for a in self._cmd]
        # Resolve the binary to an absolute path (handles .cmd shims on Windows).
        resolved = self.resolved_bin()
        if resolved:
            argv[0] = resolved
        return argv

    def complete(self, prompt: str, *, system: Optional[str] = None) -> EngineResult:
        if not self.available():
            return EngineResult(False, "", self.name, self.model(),
                                error=f"CLI '{self._bin}' not found on PATH")
        argv = self._argv()
        full_prompt = prompt if not system else f"{system}\n\n{prompt}"
        tmp_path: Optional[str] = None
        try:
            # Decode CLI output as UTF-8 explicitly. On Windows text=True would
            # otherwise use the locale codepage (cp1252) and mangle UTF-8 output
            # (em dashes etc. become "â€"").
            run_kw = dict(capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=self._timeout)
            if self._pass_via == "arg":
                argv = argv + [full_prompt]
                proc = subprocess.run(argv, **run_kw)
            else:
                # Feed the prompt from a real temp file as stdin. A piped `input=`
                # races some CLIs (e.g. `claude -p` aborts after a 3s stdin wait);
                # a file handle is available immediately and handles large prompts.
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".txt", delete=False, encoding="utf-8"
                ) as tf:
                    tf.write(full_prompt)
                    tmp_path = tf.name
                with open(tmp_path, "r", encoding="utf-8") as fin:
                    proc = subprocess.run(argv, stdin=fin, **run_kw)
        except subprocess.TimeoutExpired:
            return EngineResult(False, "", self.name, self.model(), error="CLI timed out")
        except Exception as exc:  # noqa: BLE001
            return EngineResult(False, "", self.name, self.model(), error=str(exc))
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        if proc.returncode != 0:
            return EngineResult(False, _fix_text(proc.stdout or ""), self.name, self.model(),
                                error=(proc.stderr or f"exit {proc.returncode}").strip()[:500])
        return EngineResult(True, _fix_text((proc.stdout or "").strip()), self.name, self.model())
