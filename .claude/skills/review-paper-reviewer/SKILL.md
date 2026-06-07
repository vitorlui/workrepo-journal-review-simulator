---
name: review-paper-reviewer
description: Editorial integrity, ethics, AI-use and coherence checklist for a manuscript under simulated pre-submission review. Use during the Integrity Audit step.
---

# review-paper-reviewer

This skill runs the **integrity / AI-use audit** (Step 10). It acts as an editorial
checker, **not** as a normal reviewer. It does not score scientific quality; it flags
integrity, ethics, coherence and compliance issues.

## When to use
- During the Integrity Audit step of a review, after the manuscript has been extracted.
- Whenever you need an editorial integrity pass before generating the editor decision.

## What to check
- Suspicious, incomplete, or possibly fabricated references.
- Claims without supporting evidence; exaggerated contributions.
- Inconsistencies between abstract, method, results and conclusions.
- Possible undeclared AI use and AI-use transparency.
- Data leakage and plagiarism-risk indicators.
- Dual-use concerns.
- Missing limitations and missing reproducibility details.
- Author-guideline compliance for the target venue.
- Title/abstract coherence; academic tone and clarity; figure/table clarity.
- Ethics; privacy and consent if minors are involved.
- Dataset / code / image / font / license issues.
- Acknowledgements and authorship issues.

## Output
Write `data/reviews/<review_id>/reviewer_outputs/integrity_ai_use_audit.md` with a
checklist table (check | finding | confidence) and an overall integrity assessment.

## Hard rules
- Never invent references, metrics, quartiles or policies.
- Use `NOT_VERIFIED` / `NEEDS_USER_INPUT` when something cannot be confirmed.
- Separate evidence from inference. This is a simulation, not real peer review.
