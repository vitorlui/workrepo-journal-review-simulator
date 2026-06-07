#!/usr/bin/env python3
"""Manuscript parsing/extraction CLI + the public extraction API surface.

Re-exports the spec functions (detect_input_format, validate_upload,
extract_from_markdown, extract_from_pdf, extract_from_docx, extract_from_latex,
extract_from_latex_zip, detect_main_tex_file, resolve_latex_inputs,
extract_bib_files, convert_latex_to_intermediate_markdown) and provides a CLI:

    python scripts/parse_paper.py --review-id <id> --file path/to/manuscript.tex
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.extraction import (  # noqa: F401  (re-exported for the spec surface)
    convert_latex_to_intermediate_markdown,
    detect_input_format,
    detect_main_tex_file,
    extract_bib_files,
    extract_from_docx,
    extract_from_latex,
    extract_from_latex_zip,
    extract_from_markdown,
    extract_from_pdf,
    extract_manuscript,
    resolve_latex_inputs,
    validate_upload,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse/extract a manuscript.")
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    path = Path(args.file)
    if not validate_upload(path):
        raise SystemExit(f"Unsupported or missing file: {path}")
    result = extract_manuscript(args.review_id, path)
    print(json.dumps({
        "source_format": result.source_format,
        "warnings": result.warnings,
        "fields": result.fields,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
