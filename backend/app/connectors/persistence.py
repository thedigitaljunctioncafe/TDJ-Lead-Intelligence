"""Persist connector records with workspace-scoped duplicate protection."""

import hashlib
import json
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DiscoveryRun, SearchJob, SearchSource, SourceRecord
from .base import ConnectorRecord


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    return urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path or "/",
        parsed.query,
        "",
    ))


def _content_hash(record: ConnectorRecord) -> str:
    content = "\\n".join([
        _canonical_url(record.source_url),
        (record.title or "").strip(),
        (record.excerpt or "").strip(),
    ])
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def persist_connector_records(
    db: Session,
    records: list[ConnectorRecord],
    workspace_id: str,
    search_source_id: str,
    discovery_run_id: str | None = None,
) -> dict:
    """Persist records without committing or rolling back the caller's transaction."""

    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")

    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("workspace_id must be a non-empty string")

    if not isinstance(search_source_id, str) or not search_source_id.strip():
        raise ValueError("search_source_id must be a non-empty string")

    if not isinstance(records, list):
        raise TypeError("records must be a list")

    if not all(isinstance(item, ConnectorRecord) for item in records):
        raise TypeError("every item must be a ConnectorRecord")

    source = db.get(SearchSource, search_source_id)
    if source is None:
        raise ValueError("SearchSource does not exist")
    if source.workspace_id != workspace_id:
        raise ValueError("SearchSource belongs to a different workspace")

    if discovery_run_id is not None:
        run = db.get(DiscoveryRun, discovery_run_id)
        if run is None:
            raise ValueError("DiscoveryRun does not exist")
        if run.workspace_id != workspace_id:
            raise ValueError("DiscoveryRun belongs to a different workspace")
        if run.search_job_id is None:
            raise ValueError("DiscoveryRun has no associated SearchJob")

        linked_job = db.get(SearchJob, run.search_job_id)
        if linked_job is None:
            raise ValueError("DiscoveryRun SearchJob does not exist")
        if linked_job.workspace_id != workspace_id:
            raise ValueError("DiscoveryRun SearchJob belongs to a different workspace")

    created = 0
    duplicates = 0
    seen_hashes = set()
    prepared_rows = []

    # Validate the entire batch before adding any SourceRecord to the session.
    for record in records:
        raw_data = record.raw_data

        try:
            serialized = json.dumps(raw_data, ensure_ascii=False)
        except (TypeError, ValueError):
            raise ValueError(
                "Connector raw_data must contain JSON-compatible values"
            ) from None

        if len(serialized.encode("utf-8")) > 50000:
            raise ValueError("Connector raw_data exceeds 50000 bytes")

        digest = _content_hash(record)

        if digest in seen_hashes:
            duplicates += 1
            continue

        seen_hashes.add(digest)

        existing = db.scalar(
            select(SourceRecord).where(
                SourceRecord.workspace_id == workspace_id,
                SourceRecord.content_hash == digest,
            ).limit(1)
        )

        if existing is not None:
            duplicates += 1
            continue

        prepared_rows.append(
            SourceRecord(
                workspace_id=workspace_id,
                search_source_id=search_source_id,
                discovery_run_id=discovery_run_id,
                external_id=record.external_id,
                source_url=_canonical_url(record.source_url),
                title=record.title,
                raw_excerpt=record.excerpt,
                content_hash=digest,
                published_at=record.published_at,
                collection_basis="public_source",
                attribution=record.attribution,
                raw_data_json=raw_data,
            )
        )

    for row in prepared_rows:
        db.add(row)

    created = len(prepared_rows)
    db.flush()

    return {
        "workspace_id": workspace_id,
        "search_source_id": search_source_id,
        "created": created,
        "created_source_record_ids": [row.id for row in prepared_rows],
        "duplicates_skipped": duplicates,
        "total_received": len(records),
    }
