"""Tests for the CLI engine layer (mocked subprocess; never spawns real CLIs)."""
from __future__ import annotations

from pathlib import Path

from worker.engines import cli_engine, engine_status, get_engine, query_engines, run_query


class FakeProc:
    def __init__(self, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_query_engines_order():
    assert query_engines() == ["claude", "codex", "ollama", "gemini"]


def test_available_uses_which(monkeypatch):
    eng = get_engine("ollama")
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: None)
    assert eng.available() is False
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/bin/" + b)
    assert eng.available() is True


def test_complete_stdin_substitutes_model(monkeypatch):
    eng = get_engine("ollama")  # pass_via stdin, cmd has {model}
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/bin/ollama")
    captured = {}

    def fake_run(argv, input=None, capture_output=True, text=True, timeout=None):
        captured["argv"] = argv
        captured["input"] = input
        return FakeProc(0, "REVIEW OUTPUT")

    monkeypatch.setattr(cli_engine.subprocess, "run", fake_run)
    res = eng.complete("PROMPT")
    assert res.ok and res.text == "REVIEW OUTPUT"
    assert captured["input"] == "PROMPT"          # prompt via stdin
    assert "{model}" not in " ".join(captured["argv"])  # model substituted


def test_complete_arg_appends_prompt(monkeypatch):
    eng = get_engine("codex")  # pass_via arg
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/bin/codex")
    captured = {}

    def fake_run(argv, input=None, **kw):
        captured["argv"] = argv
        captured["input"] = input
        return FakeProc(0, "OUT")

    monkeypatch.setattr(cli_engine.subprocess, "run", fake_run)
    res = eng.complete("PROMPT")
    assert res.ok
    assert captured["argv"][-1] == "PROMPT"   # prompt appended as final arg
    assert captured["input"] is None


def test_complete_nonzero_is_error(monkeypatch):
    eng = get_engine("gemini")
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: "/usr/bin/gemini")
    monkeypatch.setattr(cli_engine.subprocess, "run", lambda *a, **k: FakeProc(1, "", "boom"))
    res = eng.complete("x")
    assert res.ok is False and "boom" in (res.error or "")


def test_unavailable_cli_is_graceful(monkeypatch):
    eng = get_engine("ollama")
    monkeypatch.setattr(cli_engine.shutil, "which", lambda b: None)
    res = eng.complete("x")
    assert res.ok is False and "not found" in (res.error or "")


def test_run_query_unknown_engine():
    r = run_query("nope", "x")
    assert r.ok is False and "Unknown engine" in (r.error or "")


def test_engine_status_shape():
    st = engine_status()
    assert "claude" in st and set(st["claude"]) >= {"available", "bin", "model"}


def test_reviewer_uses_engine_when_set(monkeypatch):
    import worker.agent_orchestrator as ao
    monkeypatch.setenv("PIPELINE_ENGINE", "codex")
    monkeypatch.setattr(ao, "_call_engine",
                        lambda engine, prompt: (True, "# Engine Review\nEXCELLENT WORK", "codex-model", ""))
    out = ao.run_reviewer("REVX", "somevenue", "reviewer-methodology")
    assert out.mode == "autonomous"
    assert out.engine == "codex" and out.model == "codex-model"
    assert "EXCELLENT WORK" in out.markdown
    assert "- engine: codex" in out.markdown


def test_reviewer_falls_back_to_template_on_engine_failure(monkeypatch):
    import worker.agent_orchestrator as ao
    monkeypatch.setenv("PIPELINE_ENGINE", "gemini")
    monkeypatch.setattr(ao, "_call_engine",
                        lambda engine, prompt: (False, "", "gemini", "not installed"))
    out = ao.run_reviewer("REVX", "v", "reviewer-domain")
    assert out.mode == "offline" and out.model == "template"
    assert "offline scaffold used" in out.markdown
    assert "NEEDS_USER_INPUT" in out.markdown


def test_editor_uses_engine_when_set(monkeypatch):
    import worker.agent_orchestrator as ao
    monkeypatch.setenv("PIPELINE_ENGINE", "claude")
    monkeypatch.setattr(ao, "_call_engine",
                        lambda engine, prompt: (True, "## Decision\nminor revision", "claude-x", ""))
    out = ao.run_editor("REVX", "v", [])
    assert out.mode == "autonomous"
    assert "minor revision" in out.markdown
    assert "- engine: claude" in out.markdown


def test_template_default_is_offline(monkeypatch):
    import worker.agent_orchestrator as ao
    monkeypatch.setenv("PIPELINE_ENGINE", "template")
    out = ao.run_reviewer("REVX", "v", "reviewer-methodology")
    assert out.mode == "offline" and out.engine == "template"
    assert "do not mechanically average" not in out.markdown.lower()  # reviewer, not editor
    assert "## Scores" in out.markdown


def test_execute_query_saves_response(monkeypatch):
    import worker.run_query as rq
    from worker.engines.base import EngineResult
    from worker.reviews import create_review

    info = create_review(title="exec test")
    monkeypatch.setattr(
        rq, "run_query",
        lambda engine, prompt, system=None: EngineResult(True, "# External Review\n" + "y" * 300, engine, "m"),
    )
    out = rq.execute_query(info.review_id, "somevenue", "reviewer-domain", "claude")
    assert out["ok"] is True
    assert Path(out["stored_path"]).exists()
    assert out["stored_path"].endswith("_claude_response.md")
