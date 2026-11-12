"""Persistence layer for unified intelligence results.

The caller owns the transaction. This module never commits or rolls back.
"""

from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    DiscoveryRun,
    Entity,
    IntelligenceResult,
    Lead,
    SearchJob,
    SourceRecord,
    Workspace,
)


ENGINE_VERSION = "tdj-intelligence-v1"

RESULT_GROUPS = {
    "discovery_signals": "discovery_signal",
    "confirmed_service_intents": "confirmed_service_intent",
    "potential_opportunities": "potential_opportunity",
}


def _validate_analysis(analysis: dict) -> None:
    if not isinstance(analysis, dict):
        raise TypeError("analysis must be a dictionary")

    for group_name in RESULT_GROUPS:
        if group_name not in analysis:
            continue

        items = analysis[group_name]

        if not isinstance(items, list):
            raise TypeError(f"{group_name} must be a list")

        if not all(isinstance(item, dict) for item in items):
            raise TypeError(f"Every item in {group_name} must be a dictionary")


def _identity_for_result(
    result_type: str,
    payload: dict,
    source_record_id: str | None = None,
) -> str:
    if result_type == "discovery_signal":
        identity = payload.get("discovery_code")
    else:
        identity = payload.get("service_code")

    if not isinstance(identity, str) or not identity.strip():
        raise ValueError(
            f"Missing valid identity field for {result_type}"
        )

    # Keep results from different source records independently traceable.
    source_part = source_record_id.strip() if source_record_id else "no-source"
    key = (
        f"{result_type}:{identity.strip().casefold()}:"
        f"{source_part}"
    )

    if len(key) > 128:
        raise ValueError("Generated result key exceeds 128 characters")

    return key


def _confidence_for_result(result_type: str, payload: dict):
    if result_type == "confirmed_service_intent":
        score = payload.get("relevance_score")

        if score is None:
            return None

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("relevance_score must be numeric")

        if not 0 <= score <= 100:
            raise ValueError("relevance_score must be between 0 and 100")

        return float(score)

    return None



def _validate_workspace_reference(
    db: Session,
    model,
    record_id: str | None,
    workspace_id: str,
    label: str,
):
    """Ensure an optional reference exists and belongs to this workspace."""
    if record_id is None:
        return None

    if not isinstance(record_id, str) or not record_id.strip():
        raise ValueError(f"{label} must be a non-empty ID")

    record = db.get(model, record_id)

    if record is None:
        raise ValueError(f"{label} does not exist")

    if record.workspace_id != workspace_id:
        raise ValueError(f"{label} belongs to a different workspace")

    return record


def _validate_discovery_run(
    db: Session,
    run_id: str | None,
    workspace_id: str,
):
    run = _validate_workspace_reference(
        db, DiscoveryRun, run_id, workspace_id, "discovery_run_id"
    )

    if run is not None:
        _validate_workspace_reference(
            db,
            SearchJob,
            str(run.search_job_id),
            workspace_id,
            "DiscoveryRun.search_job_id",
        )

    return run


def _validate_source_record(
    db: Session,
    source_record_id: str | None,
    workspace_id: str,
):
    source = _validate_workspace_reference(
        db, SourceRecord, source_record_id, workspace_id, "source_record_id"
    )

    if source is not None:
        if source.entity_id:
            _validate_workspace_reference(
                db, Entity, source.entity_id, workspace_id,
                "SourceRecord.entity_id",
            )

        if source.discovery_run_id:
            _validate_discovery_run(
                db, source.discovery_run_id, workspace_id
            )

    return source


def _validate_lead(
    db: Session,
    lead_id: str | None,
    workspace_id: str,
):
    lead = _validate_workspace_reference(
        db, Lead, lead_id, workspace_id, "lead_id"
    )

    if lead is not None:
        if lead.entity_id:
            _validate_workspace_reference(
                db, Entity, lead.entity_id, workspace_id,
                "Lead.entity_id",
            )

        if lead.primary_source_record_id:
            source = _validate_workspace_reference(
                db,
                SourceRecord,
                lead.primary_source_record_id,
                workspace_id,
                "Lead.primary_source_record_id",
            )

            if source.entity_id:
                _validate_workspace_reference(
                    db, Entity, source.entity_id, workspace_id,
                    "Lead.primary_source_record_id.entity_id",
                )

            if source.discovery_run_id:
                _validate_discovery_run(
                    db, source.discovery_run_id, workspace_id
                )

            if (
                lead.entity_id
                and source.entity_id
                and lead.entity_id != source.entity_id
            ):
                raise ValueError(
                    "Lead entity does not match its primary source record entity"
                )

    return lead


def _validate_intelligence_references(
    db: Session,
    workspace_id: str,
    discovery_run_id: str | None,
    source_record_id: str | None,
    entity_id: str | None,
    lead_id: str | None,
) -> None:
    """Validate all direct and linked references before writing results."""

    _validate_discovery_run(db, discovery_run_id, workspace_id)
    source = _validate_source_record(db, source_record_id, workspace_id)

    entity = _validate_workspace_reference(
        db, Entity, entity_id, workspace_id, "entity_id"
    )

    lead = _validate_lead(db, lead_id, workspace_id)

    if source and entity and source.entity_id:
        if source.entity_id != entity.id:
            raise ValueError(
                "entity_id does not match the source record entity"
            )

    if lead and entity and lead.entity_id:
        if lead.entity_id != entity.id:
            raise ValueError(
                "entity_id does not match the lead entity"
            )

def save_intelligence_results(
    db: Session,
    analysis: dict,
    workspace_id: str,
    engine_version: str = ENGINE_VERSION,
    discovery_run_id: str | None = None,
    source_record_id: str | None = None,
    entity_id: str | None = None,
    lead_id: str | None = None,
) -> dict:
    """Insert or update intelligence results within one workspace.

    Result identity is workspace + result type + stable discovery/service code.
    Optional source/entity/run/lead references are retained on each result.

    No commit or rollback is performed. The caller controls the transaction.
    """

    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("workspace_id must be a non-empty string")

    if not isinstance(engine_version, str) or not engine_version.strip():
        raise ValueError("engine_version must be a non-empty string")

    _validate_analysis(analysis)

    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise ValueError("Workspace does not exist")

    _validate_intelligence_references(
        db=db,
        workspace_id=workspace_id,
        discovery_run_id=discovery_run_id,
        source_record_id=source_record_id,
        entity_id=entity_id,
        lead_id=lead_id,
    )

    prepared = []

    for group_name, result_type in RESULT_GROUPS.items():
        for original_payload in analysis.get(group_name, []):
            payload = deepcopy(original_payload)

            if result_type == "potential_opportunity":
                if payload.get("confirmed_intent") is not False:
                    raise ValueError(
                        "Potential opportunities must explicitly set "
                        "confirmed_intent to False"
                    )

            result_key = _identity_for_result(
                result_type, payload, source_record_id
            )
            confidence_score = _confidence_for_result(
                result_type, payload
            )

            prepared.append(
                (
                    result_type,
                    result_key,
                    payload,
                    confidence_score,
                )
            )

    # Reject duplicate identities inside the same incoming analysis.
    incoming_keys = [item[1] for item in prepared]

    if len(incoming_keys) != len(set(incoming_keys)):
        raise ValueError(
            "Analysis contains duplicate result identities"
        )

    created = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for result_type, result_key, payload, confidence_score in prepared:
        existing = db.scalar(
            select(IntelligenceResult).where(
                IntelligenceResult.workspace_id == workspace_id,
                IntelligenceResult.result_key == result_key,
            )
        )

        if existing is None:
            record = IntelligenceResult(
                workspace_id=workspace_id,
                discovery_run_id=discovery_run_id,
                source_record_id=source_record_id,
                entity_id=entity_id,
                lead_id=lead_id,
                result_type=result_type,
                result_key=result_key,
                result_payload=payload,
                engine_version=engine_version,
                confidence_score=confidence_score,
                created_at=now,
                updated_at=now,
            )
            db.add(record)
            created += 1
        else:
            existing.discovery_run_id = discovery_run_id
            existing.source_record_id = source_record_id
            existing.entity_id = entity_id
            existing.lead_id = lead_id
            existing.result_type = result_type
            existing.result_payload = payload
            existing.engine_version = engine_version
            existing.confidence_score = confidence_score
            existing.updated_at = now
            updated += 1

    # Flush checks constraints without committing the caller's transaction.
    db.flush()

    return {
        "created": created,
        "updated": updated,
        "total": created + updated,
        "workspace_id": workspace_id,
        "engine_version": engine_version,
    }
