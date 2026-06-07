"""The reviewer/editor/integrity execution seam.

For the MVP the default engine is ``template``: deterministic, offline Markdown
scaffolding built from the extracted paper + venue + reviewer profile. Every
output carries the mandatory metadata block (engine, model, mode, sources,
limitations, confidence). ``run_*`` functions are the single place to later
plug Claude API / Ollama (see model_config.yaml) without touching the pipeline.
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


def _metadata_block(review_id, venue_id, profile_id, agent_id, engine, sources) -> str:
    return "\n".join([
        "## Metadata",
        f"- review_id: {review_id}",
        f"- venue_id: {venue_id}",
        f"- agent_id: {agent_id}",
        f"- reviewer_profile: {profile_id}",
        f"- engine: {engine}",
        f"- model: {engine}",
        f"- mode: {'offline' if engine == 'template' else 'autonomous'}",
        f"- data_sources_used: {sources}",
        "- limitations: Template-generated scaffold; this is a pre-submission simulation, not real peer review. No external literature was consulted unless provided.",
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


def run_reviewer(review_id: str, venue_id: str, profile_id: str, *, agent_id: str | None = None) -> AgentOutput:
    engine = _engine()
    agent_id = agent_id or profile_id
    fields = _paper_fields(review_id)
    title = fields.get("title", "NEEDS_USER_INPUT")
    venue_name = _venue_name(venue_id)
    sources = "manuscript_extracted.md, paper_extraction.json, venue_profile.yaml"

    md = f"""# Reviewer report — {profile_id}

{_metadata_block(review_id, venue_id, profile_id, agent_id, engine, sources)}

## Submission context
- Target venue: {venue_name} ({venue_id})
- Manuscript title: {title}

## Summary
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
- This scaffold was produced by the offline template engine. Replace with a real model run (Claude/Ollama) or with imported external responses for substantive content.
"""
    return AgentOutput(agent_id, profile_id, venue_id, engine, engine, "offline" if engine == "template" else "autonomous", md)


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
    rows = "\n".join(f"| {c} | NEEDS_USER_INPUT | NOT_VERIFIED |" for c in checks)
    md = f"""# Integrity / AI-use audit

{_metadata_block(review_id, venue_id, 'integrity-ai-use-auditor', 'integrity-ai-use-auditor', engine, 'manuscript_extracted.md')}

> Acts as an editorial checker, not a normal reviewer.

## Checklist

| Check | Finding | Confidence |
| --- | --- | --- |
{rows}

## Overall integrity assessment
NEEDS_USER_INPUT
"""
    return AgentOutput("integrity-ai-use-auditor", "integrity-ai-use-auditor", venue_id, engine, engine, "offline", md)


def run_editor(review_id: str, venue_id: str, reviewer_files: list[Path]) -> AgentOutput:
    engine = _engine()
    venue_name = _venue_name(venue_id)
    reviewer_list = "\n".join(f"- {p.name}" for p in reviewer_files) or "- (none)"
    md = f"""# Editor-in-chief decision

{_metadata_block(review_id, venue_id, 'editor-in-chief', 'editor-in-chief', engine, 'reviewer_outputs/*, integrity audit, venue_profile.yaml')}

## Target venue
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
- NEEDS_USER_INPUT
"""
    return AgentOutput("editor-in-chief", "editor-in-chief", venue_id, engine, engine, "offline", md)
