"""Unified analysis pipeline: analyze text and persist intelligence results."""

from sqlalchemy.orm import Session

from .intelligence_engine import analyze_text
from .intelligence_persistence import (
    ENGINE_VERSION,
    save_intelligence_results,
)


def analyze_and_persist_text(
    db: Session,
    text: str,
    workspace_id: str,
    engine_version: str = ENGINE_VERSION,
    discovery_run_id: str | None = None,
    source_record_id: str | None = None,
    entity_id: str | None = None,
    lead_id: str | None = None,
) -> dict:
    """Analyze source text and persist its intelligence results.

    The caller owns the SQLAlchemy transaction.
    This function never commits or rolls back.

    Raw input text is not stored by this pipeline.
    """

    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("workspace_id must be a non-empty string")

    analysis = analyze_text(text)

    persistence = save_intelligence_results(
        db=db,
        analysis=analysis,
        workspace_id=workspace_id,
        engine_version=engine_version,
        discovery_run_id=discovery_run_id,
        source_record_id=source_record_id,
        entity_id=entity_id,
        lead_id=lead_id,
    )

    return {
        "analysis": analysis,
        "persistence": persistence,
        "summary": analysis["summary"],
    }
