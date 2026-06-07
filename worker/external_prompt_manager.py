"""Generate external-engine review prompts (Step 6/7).

One prompt per (review, venue, reviewer profile, engine), following the
professional template in the spec. Filenames use underscores and no ``*``
(plan deviation A2):

    prompt:   rev{n}_<profile>_<engine>_prompt.md
    response: <review_id>__<venue_id>__rev{n}_<profile>_<engine>_response.md
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from worker.markdown_store import now_iso, read_text, read_yaml, write_text
from worker.paths import load_config, review_dir, venues_dir

ENGINES = ["chatgpt", "claude", "gemini", "perplexity", "notebooklm"]


@dataclass
class GeneratedPrompt:
    review_id: str
    venue_id: str
    reviewer_profile: str
    engine: str
    prompt_path: Path
    expected_response_filename: str


def _reviewer_index(profile_id: str) -> int:
    order = {
        "reviewer-methodology": 1,
        "reviewer-domain": 2,
        "reviewer-systems-architecture": 3,
        "reviewer-reproducibility": 4,
        "reviewer-scientific-impact": 5,
    }
    return order.get(profile_id, 9)


def _load_reviewer_profile_text(profile_id: str) -> str:
    cfg = load_config("reviewer_profiles")
    for group in ("main_reviewers", "specialized_reviewers", "auditors"):
        for p in cfg.get(group, []):
            if p["id"] == profile_id:
                from worker.paths import REPO_ROOT

                md = REPO_ROOT / p.get("profile_md", "")
                if md.exists():
                    return read_text(md)
    return f"(Reviewer profile description not found for {profile_id}.)"


def _load_venue_block(venue_id: str) -> str:
    base = venues_dir() / "journals" / venue_id
    if not base.exists():
        base = venues_dir() / "conferences" / venue_id
    profile = read_yaml(base / "venue_profile.yaml") if base.exists() else {}
    name = profile.get("name", "UNKNOWN")
    lines = [f"- venue_id: {venue_id}", f"- name: {name}"]
    for key in ("type", "publisher_or_organizer", "official_url", "quartile_or_rank",
                "q1_accessibility_class", "review_rigor", "publication_speed_category"):
        if key in profile:
            lines.append(f"- {key}: {profile[key]}")
    # Append review criteria if present.
    rc = base / "review_criteria.md"
    criteria = read_text(rc) if rc.exists() else "NEEDS_USER_INPUT"
    return "\n".join(lines) + "\n\n**Review criteria:**\n\n" + criteria


def _load_paper_summary(review_id: str) -> str:
    extracted = review_dir(review_id) / "extracted" / "paper_extraction.md"
    if extracted.exists():
        return read_text(extracted)
    return "NEEDS_USER_INPUT (run extraction first)."


def _prompt_body(
    *, review_id: str, venue_id: str, venue_name: str, profile_id: str, engine: str,
    expected_filename: str, reviewer_profile_text: str, venue_block: str, paper_summary: str,
) -> str:
    return f"""You are acting as an independent scientific reviewer for a simulated pre-submission editorial review.

This is not a real peer-review process. Your goal is to help the author improve the manuscript before submission.

Review ID:
{review_id}

Target venue:
{venue_name} ({venue_id})

Engine:
{engine}

Expected output filename:
{expected_filename}

You must return your answer in Markdown. If your interface allows file generation, generate a Markdown file with the exact filename above. If not, print the full Markdown content so it can be copied and saved manually.

You are reviewing the manuscript according to the following venue information:

{venue_block}

Manuscript information:

{paper_summary}

Reviewer profile:

{reviewer_profile_text}

Your task:

1. Evaluate whether the paper fits the target venue.
2. Evaluate the paper according to your reviewer profile.
3. Identify major strengths.
4. Identify major weaknesses.
5. Identify minor weaknesses.
6. Identify missing evidence.
7. Identify unsupported or exaggerated claims.
8. Identify questions for the authors.
9. Suggest concrete revisions.
10. Provide scores by dimension.
11. Provide a final recommendation: accept | minor revision | major revision | reject | desk reject risk.
12. Indicate your confidence.
13. Separate: evidence from the manuscript / your inference / missing information / external knowledge (if used).
14. Do not invent references, venue policies, statistics, quartiles or publication times.
15. If you use external information, provide source links.
16. If you cannot verify something, write NOT_VERIFIED.

Markdown output structure:

# External Review

## Metadata
- review_id: {review_id}
- venue_id: {venue_id}
- venue_name: {venue_name}
- reviewer_profile: {profile_id}
- engine: {engine}
- expected_response_filename: {expected_filename}
- sources_used:
- confidence:

## Short summary
## Venue fit
## Major strengths
## Major weaknesses
## Minor weaknesses
## Methodological concerns
## Novelty and state of the art
## Reproducibility concerns
## Ethical or integrity concerns
## Questions for authors
## Required revisions
## Optional improvements

## Scores

| Dimension | Score 1-10 | Rationale |
| --------- | ---------: | --------- |

## Recommendation
## Confidence and limitations

## Evidence table

| Claim / issue | Evidence from manuscript | Reviewer inference | Missing information |
| ------------- | ------------------------ | ------------------ | ------------------- |

## Final notes
"""


def build_execution_prompt(review_id: str, venue_id: str, profile_id: str, engine: str) -> str:
    """Return the prompt text to feed an engine CLI for one venue×reviewer.

    Used by the Execute-query button. If a prompt file was already generated it
    is reused; otherwise it is built on the fly.
    """
    n = _reviewer_index(profile_id)
    existing = (review_dir(review_id) / "external_prompts" / "by_venue" / venue_id
                / f"rev{n}_{profile_id}_{engine}_prompt.md")
    if existing.exists():
        return read_text(existing)
    base = venues_dir() / "journals" / venue_id
    venue_profile = read_yaml(base / "venue_profile.yaml") if base.exists() else {}
    expected = f"{review_id}__{venue_id}__rev{n}_{profile_id}_{engine}_response.md"
    return _prompt_body(
        review_id=review_id, venue_id=venue_id, venue_name=venue_profile.get("name", venue_id),
        profile_id=profile_id, engine=engine, expected_filename=expected,
        reviewer_profile_text=_load_reviewer_profile_text(profile_id),
        venue_block=_load_venue_block(venue_id), paper_summary=_load_paper_summary(review_id),
    )


def generate_prompts(
    review_id: str,
    venue_ids: list[str],
    reviewer_profiles: list[str],
    engines: list[str] | None = None,
) -> list[GeneratedPrompt]:
    engines = engines or ENGINES
    generated: list[GeneratedPrompt] = []
    index_lines = [f"# External prompts index — {review_id}", "", f"_Generated {now_iso()}_", ""]

    for venue_id in venue_ids:
        venue_dir = review_dir(review_id) / "external_prompts" / "by_venue" / venue_id
        venue_dir.mkdir(parents=True, exist_ok=True)
        venue_block = _load_venue_block(venue_id)
        base = venues_dir() / "journals" / venue_id
        venue_profile = read_yaml(base / "venue_profile.yaml") if base.exists() else {}
        venue_name = venue_profile.get("name", venue_id)
        paper_summary = _load_paper_summary(review_id)
        index_lines.append(f"## Venue: {venue_name} ({venue_id})")

        for profile_id in reviewer_profiles:
            n = _reviewer_index(profile_id)
            profile_text = _load_reviewer_profile_text(profile_id)
            index_lines.append(f"- Reviewer {n} — {profile_id}")
            for engine in engines:
                expected = f"{review_id}__{venue_id}__rev{n}_{profile_id}_{engine}_response.md"
                body = _prompt_body(
                    review_id=review_id, venue_id=venue_id, venue_name=venue_name,
                    profile_id=profile_id, engine=engine, expected_filename=expected,
                    reviewer_profile_text=profile_text, venue_block=venue_block,
                    paper_summary=paper_summary,
                )
                prompt_path = venue_dir / f"rev{n}_{profile_id}_{engine}_prompt.md"
                write_text(prompt_path, body)
                generated.append(
                    GeneratedPrompt(review_id, venue_id, profile_id, engine, prompt_path, expected)
                )
                index_lines.append(f"  - {engine}: `{prompt_path.name}` -> expects `{expected}`")
        index_lines.append("")

    write_text(review_dir(review_id) / "external_prompts" / "index.md", "\n".join(index_lines))
    return generated
