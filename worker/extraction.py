"""Manuscript extraction to Markdown + structured fields.

Priority order (spec): LaTeX > Markdown > DOCX > PDF. PDF/DOCX are heuristic
for the MVP; LaTeX/Markdown are first-class. Anything not found is recorded as
``NEEDS_USER_INPUT`` (never invented).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from worker.markdown_store import now_iso, write_json, write_text
from worker.paths import review_dir

NEEDS = "NEEDS_USER_INPUT"

# Canonical extraction fields (spec, Step 2).
EXTRACTION_FIELDS = [
    "title",
    "abstract",
    "keywords",
    "research_area",
    "problem_statement",
    "claimed_contributions",
    "methodology",
    "architecture_or_system_design",
    "datasets",
    "experiments",
    "metrics",
    "baselines",
    "results_summary",
    "limitations",
    "reproducibility_artifacts",
    "ethical_considerations",
    "references",
    "paper_type",
    "likely_venue_families",
]

_SECTION_ALIASES = {
    "abstract": ["abstract"],
    "introduction": ["introduction", "1 introduction"],
    "problem_statement": ["problem statement", "motivation"],
    "methodology": ["method", "methodology", "methods", "approach", "proposed method"],
    "architecture_or_system_design": ["architecture", "system design", "system overview"],
    "experiments": ["experiments", "experimental setup", "evaluation"],
    "results_summary": ["results", "results and discussion"],
    "limitations": ["limitations", "threats to validity"],
    "datasets": ["dataset", "datasets", "data"],
    "references": ["references", "bibliography"],
    "ethical_considerations": ["ethics", "ethical considerations", "ethics statement"],
}


@dataclass
class ExtractionResult:
    source_format: str
    source_path: str
    markdown: str
    fields: dict
    warnings: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Format detection
# --------------------------------------------------------------------------- #
def detect_input_format(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".tex": "latex",
        ".md": "markdown",
        ".markdown": "markdown",
        ".docx": "docx",
        ".pdf": "pdf",
        ".zip": "latex_zip",
    }.get(ext, "unknown")


def validate_upload(path: Path) -> bool:
    return path.exists() and detect_input_format(path) != "unknown"


# --------------------------------------------------------------------------- #
# Per-format readers -> Markdown
# --------------------------------------------------------------------------- #
def extract_from_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return f"<!-- pypdf not installed; raw text extraction unavailable for {path.name} -->"
    try:
        reader = PdfReader(str(path))
        pages = [(p.extract_text() or "") for p in reader.pages]
        return "\n\n".join(pages)
    except Exception as exc:  # pragma: no cover
        return f"<!-- PDF extraction failed: {exc} -->"


def extract_from_docx(path: Path) -> str:
    try:
        import docx  # python-docx
    except Exception:
        return f"<!-- python-docx not installed; cannot extract {path.name} -->"
    try:
        document = docx.Document(str(path))
        return "\n\n".join(p.text for p in document.paragraphs)
    except Exception as exc:  # pragma: no cover
        return f"<!-- DOCX extraction failed: {exc} -->"


def detect_main_tex_file(tex_dir: Path) -> Optional[Path]:
    candidates = list(tex_dir.rglob("*.tex"))
    if not candidates:
        return None
    preferred = {"main.tex", "manuscript.tex", "paper.tex", "article.tex"}
    for c in candidates:
        if c.name.lower() in preferred:
            return c
    # Otherwise pick the file that looks like the document root.
    best, best_score = None, -1
    for c in candidates:
        try:
            text = c.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        score = sum(
            bool(re.search(pat, text))
            for pat in (r"\\documentclass", r"\\begin\{document\}", r"\\title", r"\\author")
        )
        if score > best_score:
            best, best_score = c, score
    return best


def resolve_latex_inputs(main_tex: Path, *, _depth: int = 0) -> str:
    """Inline ``\\input`` / ``\\include`` (one level deep, basic)."""
    if _depth > 8:
        return ""
    base = main_tex.parent
    text = main_tex.read_text(encoding="utf-8", errors="replace")

    def repl(match: re.Match) -> str:
        rel = match.group(1).strip()
        if not rel.endswith(".tex"):
            rel += ".tex"
        included = base / rel
        if included.exists():
            return resolve_latex_inputs(included, _depth=_depth + 1)
        return f"% [MISSING INCLUDE: {rel}]\n"

    text = re.sub(r"\\(?:input|include)\{([^}]+)\}", repl, text)
    return text


def extract_bib_files(tex_dir: Path) -> list[Path]:
    return list(tex_dir.rglob("*.bib"))


def convert_latex_to_intermediate_markdown(tex_source: str) -> str:
    """Very small LaTeX -> Markdown reducer (keeps structure, drops commands)."""
    text = tex_source
    # Title / sections.
    text = re.sub(r"\\title\{([^}]*)\}", r"# \1", text)
    text = re.sub(r"\\section\*?\{([^}]*)\}", r"## \1", text)
    text = re.sub(r"\\subsection\*?\{([^}]*)\}", r"### \1", text)
    text = re.sub(r"\\subsubsection\*?\{([^}]*)\}", r"#### \1", text)
    # Abstract environment.
    text = re.sub(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
        r"## Abstract\n\1",
        text,
        flags=re.DOTALL,
    )
    # Emphasis.
    text = re.sub(r"\\textbf\{([^}]*)\}", r"**\1**", text)
    text = re.sub(r"\\textit\{([^}]*)\}", r"*\1*", text)
    text = re.sub(r"\\emph\{([^}]*)\}", r"*\1*", text)
    # Drop comments and the most common structural commands.
    text = re.sub(r"(?m)^\s*%.*$", "", text)
    text = re.sub(r"\\(documentclass|usepackage|begin|end|maketitle|label|cite|ref)\b[^\n]*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_from_latex(path: Path) -> str:
    source = resolve_latex_inputs(path)
    return convert_latex_to_intermediate_markdown(source)


def extract_from_latex_zip(latex_dir: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    main = detect_main_tex_file(latex_dir)
    if main is None:
        return "<!-- No main .tex file found in ZIP -->", ["No main .tex file found."]
    bibs = extract_bib_files(latex_dir)
    if not bibs:
        warnings.append("No .bib file found in LaTeX source.")
    md = extract_from_latex(main)
    warnings.append(f"Main TeX detected: {main.name}")
    return md, warnings


# --------------------------------------------------------------------------- #
# Field heuristics
# --------------------------------------------------------------------------- #
def _find_section(markdown: str, aliases: list[str]) -> Optional[str]:
    lines = markdown.splitlines()
    headings = [(i, re.sub(r"^#+\s*", "", ln).strip().lower())
                for i, ln in enumerate(lines) if ln.lstrip().startswith("#")]
    for idx, (line_no, title) in enumerate(headings):
        if any(a == title or title.startswith(a) for a in aliases):
            start = line_no + 1
            end = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
            body = "\n".join(lines[start:end]).strip()
            if body:
                return body
    return None


def _extract_fields(markdown: str) -> dict:
    fields = {f: NEEDS for f in EXTRACTION_FIELDS}

    # Title = first level-1 heading.
    m = re.search(r"(?m)^#\s+(.+)$", markdown)
    if m:
        fields["title"] = m.group(1).strip()

    for field_name, aliases in _SECTION_ALIASES.items():
        body = _find_section(markdown, aliases)
        if body:
            if field_name == "introduction":
                if fields["problem_statement"] == NEEDS:
                    fields["problem_statement"] = body[:1200]
            elif field_name in fields:
                fields[field_name] = body[:2000]

    # Keywords line.
    km = re.search(r"(?im)^\**keywords?\**[:\-]\s*(.+)$", markdown)
    if km:
        fields["keywords"] = km.group(1).strip()

    return fields


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def extract_manuscript(review_id: str, source_path: Path) -> ExtractionResult:
    """Extract a manuscript and write the standard artefacts."""
    fmt = detect_input_format(source_path)
    warnings: list[str] = []

    if fmt == "latex":
        markdown = extract_from_latex(source_path)
    elif fmt == "markdown":
        markdown = extract_from_markdown(source_path)
    elif fmt == "docx":
        markdown = extract_from_docx(source_path)
    elif fmt == "pdf":
        markdown = extract_from_pdf(source_path)
    elif fmt == "latex_zip":
        markdown, warnings = extract_from_latex_zip(source_path)
    else:
        markdown = f"<!-- Unknown format for {source_path.name} -->"
        warnings.append("Unknown manuscript format.")

    fields = _extract_fields(markdown)
    result = ExtractionResult(
        source_format=fmt,
        source_path=str(source_path),
        markdown=markdown,
        fields=fields,
        warnings=warnings,
    )
    _write_artifacts(review_id, result)
    return result


def _write_artifacts(review_id: str, result: ExtractionResult) -> None:
    root = review_dir(review_id) / "extracted"
    write_text(root / "manuscript_extracted.md", result.markdown)

    payload = {
        "review_id": review_id,
        "source_format": result.source_format,
        "source_path": result.source_path,
        "extracted_at": now_iso(),
        "fields": result.fields,
        "warnings": result.warnings,
    }
    write_json(root / "paper_extraction.json", payload)

    md_lines = [f"# Paper extraction — {review_id}", "", f"_Source format: {result.source_format}_", ""]
    for fname in EXTRACTION_FIELDS:
        md_lines.append(f"## {fname}")
        md_lines.append(str(result.fields.get(fname, NEEDS)))
        md_lines.append("")
    write_text(root / "paper_extraction.md", "\n".join(md_lines))

    if result.source_format in ("latex", "latex_zip"):
        report = [f"# LaTeX extraction report — {review_id}", ""]
        report += [f"- {w}" for w in (result.warnings or ["(no warnings)"])]
        write_text(root / "latex_extraction_report.md", "\n".join(report) + "\n")
