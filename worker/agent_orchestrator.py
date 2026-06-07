"""The reviewer/editor/integrity execution seam.

Default engine is ``template``: deterministic, offline Markdown scaffolding built
from the extracted paper + venue + reviewer profile. When ``PIPELINE_ENGINE``
(env) or ``pipeline.default_engine`` names a real engine (``claude``, ``codex``,
``ollama``, ``gemini``) whose CLI is installed, the agent instead runs that CLI
with a built prompt and uses its Markdown output. If the engine is unavailable
or errors, it falls back to the offline scaffold so the pipeline never breaks.

Every output carries the mandatory metadata block (engine, model, mode, sources,
limitations, confidence).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from worker.markdown_store import now_iso, read_text, read_yaml
from worker.paths import load_config, review_dir, venues_dir

NOT_VERIFIED = "NOT_VERIFIED"


@dataclass
class AgentOutput:
    agent_id: str
    reviewer_profile: str
    venue_id: str
    engine: str
    model: str
    mode: str
    markdown: str


def _engine() -> str:
    return os.environ.get("PIPELINE_ENGINE") or load_config("pipeline").get("default_engine", "template")


def _call_engine(engine: str, prompt: str) -> tuple[bool, str, str, str]:
    """Run a real engine CLI. Returns (ok, text, model, error)."""
    try:
        from worker.engines import get_engine, run_query
    except Exception as exc:  # pragma: no cover
        return False, "", engine, f"engine layer unavailable: {exc}"
    eng = get_engine(engine)
    if eng is None:
        return False, "", engine, f"unknown engine '{engine}'"
    if not eng.available():
        return False, "", eng.model(), f"CLI for '{engine}' not installed/available"
    res = run_query(engine, prompt)
    return res.ok, res.text or "", res.model, res.error or ""


def _metadata_block(review_id, venue_id, profile_id, agent_id, engine, sources,
                    *, model: str | None = None, mode: str | None = None) -> str:
    model = model or engine
    mode = mode or ("offline" if engine == "template" else "autonomous")
    return "\n".join([
        "## Metadata",
        f"- review_id: {review_id}",
        f"- venue_id: {venue_id}",
        f"- agent_id: {agent_id}",
        f"- reviewer_profile: {profile_id}",
        f"- engine: {engine}",
        f"- model: {model}",
        f"- mode: {mode}",
        f"- data_sources_used: {sources}",
        "- limitations: Pre-submission simulation, not real peer review. The offline template engine "
        "produces a scaffold; a real engine produces substantive content but may still err.",
        f"- confidence: {NOT_VERIFIED}",
        f"- generated_at: {now_iso()}",
    ])


def _paper_fields(review_id: str) -> dict:
    data = read_yaml(review_dir(review_id) / "extracted" / "paper_extraction.json")
    return data.get("fields", {}) if data else {}


def _venue_name(venue_id: str) -> str:
    base = venues_dir() / "journals" / venue_id
    profile = read_yaml(base / "venue_profile.yaml") if base.exists() else {}
    return profile.get("name", venue_id)


def _scores_table() -> str:
    rubric = load_config("scoring_rubrics")
    rows = ["| Dimension | Score 1-10 | Rationale |", "| --- | ---: | --- |"]
    for d in rubric.get("dimensions", []):
        rows.append(f"| {d['label']} | {NOT_VERIFIED} | NEEDS_USER_INPUT |")
    return "\n".join(rows)


# --------------------------------------------------------------------------- #
# Scaffold bodies (offline template engine)
# --------------------------------------------------------------------------- #
def _reviewer_scaffold_body() -> str:
    return f"""## Summary
NEEDS_USER_INPUT — concise neutral summary of the manuscript as understood from the extraction.

## Venue fit (provisional)
Venue data may be incomplete; this assessment is PROVISIONAL. NEEDS_USER_INPUT.

## Major strengths
- NEEDS_USER_INPUT

## Major weaknesses
- NEEDS_USER_INPUT

## Minor weaknesses
- NEEDS_USER_INPUT

## Questions for authors
- NEEDS_USER_INPUT

## Required revisions
- NEEDS_USER_INPUT

## Optional improvements
- NEEDS_USER_INPUT

## Scores
{_scores_table()}

## Recommendation
NEEDS_USER_INPUT (accept | minor revision | major revision | reject | desk reject risk)

## Evidence table

| Claim / issue | Evidence from manuscript | Reviewer inference | Missing information |
| --- | --- | --- | --- |
| NEEDS_USER_INPUT | NEEDS_USER_INPUT | NEEDS_USER_INPUT | NEEDS_USER_INPUT |

## Missing information
- NEEDS_USER_INPUT

## Confidence and limitations
- confidence: {NOT_VERIFIED}
- This scaffold was produced by the offline template engine. Set PIPELINE_ENGINE to a real
  engine (claude/codex/ollama/gemini) or import external responses for substantive content."""


# --------------------------------------------------------------------------- #
# Agents
# --------------------------------------------------------------------------- #
def run_reviewer(review_id: str, venue_id: str, profile_id: str, *, agent_id: str | None = None) -> AgentOutput:
    engine = _engine()
    agent_id = agent_id or profile_id
    fields = _paper_fields(review_id)
    title = fields.get("title", "NEEDS_USER_INPUT")
    venue_name = _venue_name(venue_id)
    sources = "manuscript_extracted.md, paper_extraction.json, venue_profile.yaml"

    model, mode = engine, "offline"
    if engine == "template":
        body = _reviewer_scaffold_body()
    else:
        from worker.external_prompt_manager import build_execution_prompt
        prompt = build_execution_prompt(review_id, venue_id, profile_id, engine)
        ok, text, model, err = _call_engine(engine, prompt)
        if ok and text.strip():
            body, mode = text, "autonomous"
        else:
            body = (f"> Engine '{engine}' unavailable or failed ({err}); offline scaffold used.\n\n"
                    + _reviewer_scaffold_body())
            model, mode = "template", "offline"

    header = (
        f"# Reviewer report — {profile_id}\n\n"
        + _metadata_block(review_id, venue_id, profile_id, agent_id, engine, sources, model=model, mode=mode)
        + f"\n\n## Submission context\n- Target venue: {venue_name} ({venue_id})\n- Manuscript title: {title}\n\n"
    )
    return AgentOutput(agent_id, profile_id, venue_id, engine, model, mode, header + body)


def run_integrity(review_id: str, venue_id: str) -> AgentOutput:
    engine = _engine()
    checks = [
        "suspicious or incomplete references", "possibly fabricated references",
        "unsupported claims", "abstract/method/results/conclusion inconsistencies",
        "exaggerated contributions", "possible undeclared AI use",
        "data leakage", "plagiarism risk indicators", "dual-use concerns",
        "missing limitations", "missing reproducibility details",
        "author-guideline compliance", "title/abstract coherence", "tone and clarity",
        "ethical issues", "privacy/consent if minors are involved",
        "dataset/code/license issues",
    ]
    model, mode = engine, "offline"
    if engine == "template":
        rows = "\n".join(f"| {c} | NEEDS_USER_INPUT | NOT_VERIFIED |" for c in checks)
        body = ("## Checklist\n\n| Check | Finding | Confidence |\n| --- | --- | --- |\n"
                + rows + "\n\n## Overall integrity assessment\nNEEDS_USER_INPUT")
    else:
        prompt = _integrity_prompt(review_id, venue_id, checks)
        ok, text, model, err = _call_engine(engine, prompt)
        if ok and text.strip():
            body, mode = text, "autonomous"
        else:
            rows = "\n".join(f"| {c} | NEEDS_USER_INPUT | NOT_VERIFIED |" for c in checks)
            body = (f"> Engine '{engine}' unavailable or failed ({err}); offline scaffold used.\n\n"
                    "## Checklist\n\n| Check | Finding | Confidence |\n| --- | --- | --- |\n" + rows)
            model, mode = "template", "offline"

    header = ("# Integrity / AI-use audit\n\n"
              + _metadata_block(review_id, venue_id, "integrity-ai-use-auditor",
                                "integrity-ai-use-auditor", engine, "manuscript_extracted.md",
                                model=model, mode=mode)
              + "\n\n> Acts as an editorial checker, not a normal reviewer.\n\n")
    return AgentOutput("integrity-ai-use-auditor", "integrity-ai-use-auditor", venue_id, engine, model, mode, header + body)


def run_editor(review_id: str, venue_id: str, reviewer_files: list[Path]) -> AgentOutput:
    engine = _engine()
    venue_name = _venue_name(venue_id)
    reviewer_list = "\n".join(f"- {p.name}" for p in reviewer_files) or "- (none)"

    model, mode = engine, "offline"
    scaffold = f"""## Target venue
{venue_name} ({venue_id})

## Reviews considered
{reviewer_list}

## Synthesis of disagreements
NEEDS_USER_INPUT — do NOT mechanically average scores. Explain where reviewers disagree and why.

## Decisive weaknesses
- NEEDS_USER_INPUT

## Real strengths
- NEEDS_USER_INPUT

## Venue suitability
PROVISIONAL — NEEDS_USER_INPUT. Consider redirection to another venue if appropriate.

## Decision
NEEDS_USER_INPUT (desk reject | reject | major revision | minor revision | accept)

## What must change for this paper to be acceptable
- NEEDS_USER_INPUT"""

    if engine != "template":
        prompt = _editor_prompt(review_id, venue_id, venue_name, reviewer_files)
        ok, text, model, err = _call_engine(engine, prompt)
        if ok and text.strip():
            scaffold, mode = text, "autonomous"
        else:
            scaffold = f"> Engine '{engine}' unavailable or failed ({err}); offline scaffold used.\n\n" + scaffold
            model, mode = "template", "offline"

    md = ("# Editor-in-chief decision\n\n"
          + _metadata_block(review_id, venue_id, "editor-in-chief", "editor-in-chief", engine,
                            "reviewer_outputs/*, integrity audit, venue_profile.yaml",
                            model=model, mode=mode)
          + "\n\n" + scaffold + "\n")
    return AgentOutput("editor-in-chief", "editor-in-chief", venue_id, engine, model, mode, md)


# --------------------------------------------------------------------------- #
# Prompt builders for the real-engine path
# --------------------------------------------------------------------------- #
def _paper_summary(review_id: str) -> str:
    p = review_dir(review_id) / "extracted" / "paper_extraction.md"
    return read_text(p) if p.exists() else "NEEDS_USER_INPUT (no extraction)"


def _integrity_prompt(review_id: str, venue_id: str, checks: list[str]) -> str:
    bullet = "\n".join(f"- {c}" for c in checks)
    return f"""You are an editorial integrity checker for a simulated pre-submission review (not a reviewer).
Review ID: {review_id}. Venue: {venue_id}.

Manuscript extraction:
{_paper_summary(review_id)}

Check for the following and report findings as a Markdown table (Check | Finding | Confidence),
then an overall integrity assessment:
{bullet}

Rules: do not invent references, metrics or policies. Use NOT_VERIFIED / NEEDS_USER_INPUT when
something cannot be confirmed. Separate evidence from inference. Output Markdown only."""


def _editor_prompt(review_id: str, venue_id: str, venue_name: str, reviewer_files: list[Path]) -> str:
    reports = []
    for p in reviewer_files[:12]:
        try:
            reports.append(f"### {p.name}\n{read_text(p)[:4000]}")
        except Exception:
            continue
    joined = "\n\n".join(reports) or "(no reviewer reports found)"
    return f"""You are the Editor-in-Chief for a simulated pre-submission editorial review.
Review ID: {review_id}. Target venue: {venue_name} ({venue_id}).

Manuscript extraction:
{_paper_summary(review_id)}

Independent reviewer reports:
{joined}

Produce Markdown with these sections: Target venue, Reviews considered, Synthesis of
disagreements, Decisive weaknesses, Real strengths, Venue suitability, Decision
(desk reject | reject | major revision | minor revision | accept), and "What must change for
this paper to be acceptable".

Rules: explain disagreements; identify decisive weaknesses and real strengths; recommend a
different venue if appropriate; separate mandatory revisions from optional improvements; do NOT
mechanically average scores; do not invent references or metrics. Output Markdown only."""
