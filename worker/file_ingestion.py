"""Safe file ingestion.

Validates uploads (extension, real MIME via pure-Python magic bytes, size),
renames them to a safe internal name, computes SHA256, stores the original,
extracts ZIPs in a sandbox with path-traversal/executable blocking, writes an
``upload_report.md`` and registers hashes in ``audit/file_hashes.json``.

MIME validation uses the pure-Python ``filetype`` library + ``mimetypes``
(plan deviation B3) so it works natively on Windows without libmagic.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from worker.markdown_store import now_iso, slugify
from worker.paths import load_config, review_dir

try:  # pure-Python magic bytes; optional
    import filetype  # type: ignore
except Exception:  # pragma: no cover
    filetype = None


@dataclass
class IngestResult:
    ok: bool
    original_filename: str
    stored_path: Optional[Path]
    extension: str
    mime_type: str
    size_bytes: int
    sha256: str
    kind: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    extracted_dir: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "original_filename": self.original_filename,
            "stored_path": str(self.stored_path) if self.stored_path else None,
            "extension": self.extension,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "kind": self.kind,
            "warnings": self.warnings,
            "errors": self.errors,
            "extracted_dir": str(self.extracted_dir) if self.extracted_dir else None,
        }


def _policy() -> dict:
    return load_config("upload_policy")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _detect_mime(data: bytes, ext: str) -> str:
    policy = _policy()
    if ext in set(policy.get("text_extensions", [])):
        # Text formats have no reliable magic bytes; trust extension if decodable.
        try:
            data.decode("utf-8")
            return mimetypes.types_map.get(ext, "text/plain")
        except UnicodeDecodeError:
            return "application/octet-stream"
    if filetype is not None:
        kind = filetype.guess(data)
        if kind is not None:
            return kind.mime
    guessed, _ = mimetypes.guess_type(f"x{ext}")
    return guessed or "application/octet-stream"


def _mime_allowed_for_ext(ext: str, mime: str) -> bool:
    policy = _policy()
    groups = policy.get("mime_groups", {})
    if ext in set(policy.get("text_extensions", [])):
        return True
    ext_to_group = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".zip": "zip",
    }
    group = ext_to_group.get(ext)
    if group is None:
        return True  # bib/csv handled as text; others permissive
    return mime in set(groups.get(group, []))


def ingest_file(
    review_id: str,
    *,
    original_filename: str,
    data: bytes,
    kind: str = "manuscript",
) -> IngestResult:
    """Validate and store a single uploaded file for ``review_id``."""
    policy = _policy()
    allowed = set(policy.get("allowed_extensions", []))
    max_bytes = int(policy.get("max_upload_mb", 50)) * 1024 * 1024

    ext = Path(original_filename).suffix.lower()
    size = len(data)
    sha = _sha256(data)
    mime = _detect_mime(data, ext)

    result = IngestResult(
        ok=True,
        original_filename=original_filename,
        stored_path=None,
        extension=ext,
        mime_type=mime,
        size_bytes=size,
        sha256=sha,
        kind=kind,
    )

    if ext not in allowed:
        result.ok = False
        result.errors.append(f"Extension '{ext}' is not allowed.")
    if size > max_bytes:
        result.ok = False
        result.errors.append(f"File too large ({size} bytes > {max_bytes} bytes).")
    if not _mime_allowed_for_ext(ext, mime):
        result.ok = False
        result.errors.append(f"Detected MIME '{mime}' does not match extension '{ext}'.")

    root = review_dir(review_id)
    dest_subdir = {
        "manuscript": "input/original",
        "previous_review": "input/previous_reviews",
        "author_response": "input/author_response",
    }.get(kind, "input/original")

    if result.ok:
        safe_name = f"{slugify(Path(original_filename).stem)}-{sha[:8]}{ext}"
        stored = root / dest_subdir / safe_name
        stored.parent.mkdir(parents=True, exist_ok=True)
        stored.write_bytes(data)
        result.stored_path = stored

        if ext == ".zip":
            extracted = root / "input" / "latex_source"
            warn, err = _safe_extract_zip(stored, extracted)
            result.warnings.extend(warn)
            if err:
                result.errors.extend(err)
                result.ok = False
            else:
                result.extracted_dir = extracted

    _register_hash(review_id, result)
    _write_upload_report(review_id, result)
    return result


def _safe_extract_zip(zip_path: Path, dest: Path) -> tuple[list[str], list[str]]:
    policy = _policy().get("zip_policy", {})
    warnings: list[str] = []
    errors: list[str] = []
    blocked_ext = set(policy.get("blocked_inner_extensions", []))
    max_entries = int(policy.get("max_entries", 5000))
    max_uncompressed = int(policy.get("max_uncompressed_mb", 500)) * 1024 * 1024

    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()

    try:
        with zipfile.ZipFile(zip_path) as zf:
            infos = zf.infolist()
            if len(infos) > max_entries:
                errors.append(f"ZIP has too many entries ({len(infos)} > {max_entries}).")
                return warnings, errors
            total = sum(i.file_size for i in infos)
            if total > max_uncompressed:
                errors.append("ZIP uncompressed size exceeds the configured limit.")
                return warnings, errors

            for info in infos:
                name = info.filename
                if name.endswith("/"):
                    continue
                # Block absolute paths and traversal.
                if Path(name).is_absolute() or name.startswith("/") or ".." in Path(name).parts:
                    errors.append(f"Blocked unsafe path inside ZIP: {name}")
                    continue
                target = (dest / name).resolve()
                if not str(target).startswith(str(dest_resolved)):
                    errors.append(f"Blocked path traversal inside ZIP: {name}")
                    continue
                inner_ext = Path(name).suffix.lower()
                if inner_ext in blocked_ext:
                    errors.append(f"Blocked executable/dangerous file inside ZIP: {name}")
                    continue
                if Path(name).name.startswith(".") and policy.get("warn_on_hidden_files", True):
                    warnings.append(f"Hidden file inside ZIP: {name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    out.write(src.read())
    except zipfile.BadZipFile:
        errors.append("Uploaded file is not a valid ZIP archive.")
    return warnings, errors


def _register_hash(review_id: str, result: IngestResult) -> None:
    path = review_dir(review_id) / "audit" / "file_hashes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        registry = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError:
        registry = {}
    registry[result.sha256] = {
        "original_filename": result.original_filename,
        "stored_path": str(result.stored_path) if result.stored_path else None,
        "size_bytes": result.size_bytes,
        "mime_type": result.mime_type,
        "kind": result.kind,
        "registered_at": now_iso(),
    }
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def _write_upload_report(review_id: str, result: IngestResult) -> None:
    path = review_dir(review_id) / "input" / "upload_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "OK" if result.ok else "REJECTED"
    lines = [
        f"### Upload {result.original_filename} — {status} ({now_iso()})",
        "",
        f"- kind: {result.kind}",
        f"- extension: {result.extension}",
        f"- mime_type: {result.mime_type}",
        f"- size_bytes: {result.size_bytes}",
        f"- sha256: {result.sha256}",
        f"- stored_path: {result.stored_path}",
    ]
    if result.extracted_dir:
        lines.append(f"- extracted_dir: {result.extracted_dir}")
    if result.warnings:
        lines.append("- warnings:")
        lines += [f"  - {w}" for w in result.warnings]
    if result.errors:
        lines.append("- errors:")
        lines += [f"  - {e}" for e in result.errors]
    lines.append("")
    header = ""
    if not path.exists():
        header = f"# Upload report — {review_id}\n\n"
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n".join(lines) + "\n")
