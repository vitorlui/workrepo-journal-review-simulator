"""Database layer: SQLAlchemy 2.0 models + session factory.

The DB is an *index and workflow-state manager only* — the Markdown/YAML files
remain the semantic memory. Models live here in the shared core library (C6) so
the API, the worker and the scripts all use one definition. ``db/schema.sql`` is
a generated reference snapshot of these models (C9).

Local runs fall back to a SQLite file when ``DATABASE_URL`` is unset (B4);
Docker provides PostgreSQL.
"""
from __future__ import annotations

import contextlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from worker.paths import REPO_ROOT, data_dir


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    # Naive UTC to match TIMESTAMP WITHOUT TIME ZONE columns.
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# Models (minimum fields per spec; the DB indexes the documental memory)
# --------------------------------------------------------------------------- #
class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), default="UNKNOWN")
    status: Mapped[str] = mapped_column(String(64), default="created")
    submission_type: Mapped[str] = mapped_column(String(64), default="new_submission")
    selected_venue_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    paper_type: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    detected_areas: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    final_decision: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    path_on_disk: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Paper(Base):
    __tablename__ = "papers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512), default="UNKNOWN")
    abstract: Mapped[str] = mapped_column(Text, default="")
    paper_type: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    detected_areas: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    stored_filename: Mapped[str] = mapped_column(String(512))
    extension: Mapped[str] = mapped_column(String(32), default="")
    mime_type: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    kind: Mapped[str] = mapped_column(String(64), default="manuscript")
    path_on_disk: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ExtractedDocument(Base):
    __tablename__ = "extracted_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(64), default="manuscript_extracted")
    path_on_disk: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512), default="UNKNOWN")
    acronym: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    type: Mapped[str] = mapped_column(String(64), default="journal")
    venue_family: Mapped[str] = mapped_column(String(256), default="UNKNOWN")
    quartile_or_rank: Mapped[str] = mapped_column(Text, default="UNKNOWN")
    q1_accessibility_class: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    publication_speed_category: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    review_rigor: Mapped[str] = mapped_column(String(128), default="UNKNOWN")
    official_url: Mapped[str] = mapped_column(Text, default="UNKNOWN")
    path_on_disk: Mapped[str] = mapped_column(Text, default="")
    source_ref: Mapped[str] = mapped_column(Text, default="")
    last_verified_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class VenueFile(Base):
    __tablename__ = "venue_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_id: Mapped[str] = mapped_column(String(128), index=True)
    file_kind: Mapped[str] = mapped_column(String(64), default="")
    path_on_disk: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class LiteratureItem(Base):
    __tablename__ = "literature_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    citation_key: Mapped[str] = mapped_column(String(256), default="")
    title: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[str] = mapped_column(String(16), default="")
    venue: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class RecentPaper(Base):
    __tablename__ = "recent_papers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, default="UNKNOWN")
    area: Mapped[str] = mapped_column(String(256), default="")
    marker: Mapped[str] = mapped_column(String(64), default="")  # foundational/sota/...
    path_on_disk: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ReviewerProfile(Base):
    __tablename__ = "reviewer_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    kind: Mapped[str] = mapped_column(String(32), default="main")
    path_on_disk: Mapped[str] = mapped_column(Text, default="")


class ExternalEngine(Base):
    __tablename__ = "external_engines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    engine_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    mode: Mapped[str] = mapped_column(String(64), default="manual_external_prompt")


class ExternalPrompt(Base):
    __tablename__ = "external_prompts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    venue_id: Mapped[str] = mapped_column(String(128), default="")
    reviewer_profile: Mapped[str] = mapped_column(String(128), default="")
    engine: Mapped[str] = mapped_column(String(64), default="")
    prompt_file_path: Mapped[str] = mapped_column(Text, default="")
    expected_response_filename: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ExternalResponse(Base):
    __tablename__ = "external_responses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    venue_id: Mapped[str] = mapped_column(String(128), default="")
    reviewer_profile: Mapped[str] = mapped_column(String(128), default="")
    engine: Mapped[str] = mapped_column(String(64), default="")
    response_file_path: Mapped[str] = mapped_column(Text, default="")
    has_sources: Mapped[bool] = mapped_column(Boolean, default=False)
    looks_incomplete: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="imported")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class InternalAgentRun(Base):
    __tablename__ = "internal_agent_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    venue_id: Mapped[str] = mapped_column(String(128), default="")
    agent_id: Mapped[str] = mapped_column(String(128), default="")
    reviewer_profile: Mapped[str] = mapped_column(String(128), default="")
    engine: Mapped[str] = mapped_column(String(64), default="template")
    model: Mapped[str] = mapped_column(String(128), default="template")
    mode: Mapped[str] = mapped_column(String(64), default="offline")
    output_path: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PendingRequest(Base):
    __tablename__ = "pending_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pending_id: Mapped[str] = mapped_column(String(64), index=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    venue_id: Mapped[str] = mapped_column(String(128), default="")
    agent_id: Mapped[str] = mapped_column(String(128), default="")
    reviewer_profile: Mapped[str] = mapped_column(String(128), default="")
    request_type: Mapped[str] = mapped_column(String(64), default="clarification required")
    question: Mapped[str] = mapped_column(Text, default="")
    suggested_engine: Mapped[str] = mapped_column(String(64), default="")
    generated_prompt_path: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="open")
    iteration_number: Mapped[int] = mapped_column(Integer, default=1)
    max_iterations: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class EditorialDecision(Base):
    __tablename__ = "editorial_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    venue_id: Mapped[str] = mapped_column(String(128), default="")
    decision: Mapped[str] = mapped_column(String(64), default="UNKNOWN")
    decision_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# --------------------------------------------------------------------------- #
# Engine / session management
# --------------------------------------------------------------------------- #
_engine = None
_SessionLocal: Optional[sessionmaker] = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # Local SQLite fallback (B4).
    db_path = data_dir() / "jrs_local.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        url = database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, connect_args=connect_args)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def init_db(seed: bool = True) -> None:
    """Create tables idempotently and optionally seed static rows."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    if seed:
        seed_static_rows()


@contextlib.contextmanager
def session_scope() -> Iterator[Session]:
    get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def seed_static_rows() -> None:
    """Seed external engines + reviewer profiles from config (idempotent)."""
    from worker.paths import load_config

    engines = load_config("external_engines").get("engines", [])
    profiles_cfg = load_config("reviewer_profiles")
    with session_scope() as s:
        for e in engines:
            exists = s.scalar(select(ExternalEngine).where(ExternalEngine.engine_id == e["id"]))
            if not exists:
                s.add(ExternalEngine(engine_id=e["id"], name=e.get("name", ""), mode=e.get("mode", "")))
        for group, kind in (
            ("main_reviewers", "main"),
            ("specialized_reviewers", "specialized"),
            ("auditors", "auditor"),
        ):
            for p in profiles_cfg.get(group, []):
                exists = s.scalar(
                    select(ReviewerProfile).where(ReviewerProfile.profile_id == p["id"])
                )
                if not exists:
                    s.add(
                        ReviewerProfile(
                            profile_id=p["id"],
                            title=p.get("title", ""),
                            kind=kind,
                            path_on_disk=str(REPO_ROOT / p.get("profile_md", "")),
                        )
                    )


def log_audit(review_id: str, event_type: str, message: str) -> None:
    """Append an audit event row (best-effort; never raises into the pipeline)."""
    try:
        with session_scope() as s:
            s.add(AuditEvent(review_id=review_id, event_type=event_type, message=message))
    except Exception:
        pass
