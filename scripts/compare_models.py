#!/usr/bin/env python3
"""Compare reviewer outputs across providers (claude | ollama | template).

    python scripts/compare_models.py --review-id <id> --provider ollama \\
        --model llama3.1 --input-prompt path/to/prompt.md --output-file out.md

For the MVP this writes a comparison scaffold (the offline template engine does
not call external models). It records provider/model and a comparison rubric so
real runs can be dropped in later. Outputs go to
data/reviews/<id>/reviewer_outputs/model_comparison/.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.markdown_store import now_iso, write_text
from worker.paths import load_config, review_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare model outputs.")
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--provider", default="ollama", choices=["claude", "ollama", "template"])
    parser.add_argument("--model", default="llama3.1")
    parser.add_argument("--input-prompt", help="Path to a prompt file.")
    parser.add_argument("--output-file", help="Filename to write under model_comparison/.")
    args = parser.parse_args()

    out_dir = review_dir(args.review_id) / "reviewer_outputs" / "model_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.output_file or f"{args.provider}_{args.model}.md"
    dims = load_config("model_config").get("comparison", {}).get("dimensions", [])

    body = [
        f"# Model comparison output — {args.provider} / {args.model}",
        "",
        f"- generated_at: {now_iso()}",
        f"- input_prompt: {args.input_prompt or 'NEEDS_USER_INPUT'}",
        "",
        "## Comparison dimensions",
    ]
    body += [f"- {d}: NEEDS_USER_INPUT" for d in dims]
    body += ["", "## Model output", "",
             "NEEDS_USER_INPUT — paste the model's review here, or wire up a live provider in agent_orchestrator.py."]
    path = out_dir / out_name
    write_text(path, "\n".join(body))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
