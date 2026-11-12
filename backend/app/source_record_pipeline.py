"""SourceRecord integration for the unified intelligence pipeline."""

from sqlalchemy.orm import Session

from .intelligence_pipeline import analyze_and_persist_text
from .models import SourceRecord


def analyze_source_record(
    db: Session,
    source_record_id: str,
    workspace_id: str,
    lead_id: str | None = None,
    engine_version: str | None = None,
) -> dict:
    """Analyze a stored SourceRecord excerpt and persist attributed results.

    The caller owns the transaction. No commit or rollback is performed.
    """

    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")

    if not isinstance(source_record_id, str) or not source_record_id.strip():
        raise ValueError("source_record_id must be a non-empty string")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("workspace_id must be a non-empty string")

    source = db.get(SourceRecord, source_record_id)

    if source is None:
        raise ValueError("SourceRecord does not exist")

    if source.workspace_id != workspace_id:
        raise ValueError("SourceRecord belongs to a different workspace")

    if not isinstance(source.raw_excerpt, str) or not source.raw_excerpt.strip():
        raise ValueError("SourceRecord.raw_excerpt must contain analyzable text")

    kwargs = {
        "db": db,
        "text": source.raw_excerpt,
        "workspace_id": workspace_id,
        "discovery_run_id": source.discovery_run_id,
        "source_record_id": source.id,
        "entity_id": source.entity_id,
        "lead_id": lead_id,
    }

    if engine_version is not None:
        kwargs["engine_version"] = engine_version

    result = analyze_and_persist_text(**kwargs)
    result["source_record_id"] = source.id
    return result
