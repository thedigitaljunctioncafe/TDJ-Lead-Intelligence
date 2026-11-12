"""Transaction-controlled SearchJob to intelligence execution pipeline."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DiscoveryRun, SearchJob, SearchJobSource, SearchSource
from ..source_record_pipeline import analyze_source_record
from .base import ConnectorContext
from .persistence import persist_connector_records
from .rate_limit import RateLimiter
from .registry import ConnectorRegistry
from .service import collect_from_search_source


def execute_discovery_job(
    db: Session,
    search_job_id: int,
    registry: ConnectorRegistry,
    rate_limiter: RateLimiter,
    max_records_per_source: int = 50,
) -> dict:
    """Execute linked sources. The caller owns commit and rollback."""

    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")
    if isinstance(search_job_id, bool) or not isinstance(search_job_id, int):
        raise TypeError("search_job_id must be an integer")
    if not isinstance(registry, ConnectorRegistry):
        raise TypeError("registry must be a ConnectorRegistry")
    if not isinstance(rate_limiter, RateLimiter):
        raise TypeError("rate_limiter must be a RateLimiter")
    if isinstance(max_records_per_source, bool) or not isinstance(max_records_per_source, int):
        raise TypeError("max_records_per_source must be an integer")
    if not 1 <= max_records_per_source <= 500:
        raise ValueError("max_records_per_source must be between 1 and 500")

    job = db.get(SearchJob, search_job_id)
    if job is None:
        raise ValueError("SearchJob does not exist")
    if not isinstance(job.query, str) or not job.query.strip():
        raise ValueError("SearchJob query must not be empty")
    if job.status == "running":
        raise ValueError("SearchJob is already running")

    links = db.scalars(
        select(SearchJobSource)
        .where(SearchJobSource.search_job_id == job.id)
        .order_by(SearchJobSource.id)
    ).all()

    if not links:
        raise ValueError("SearchJob has no linked sources")

    run = DiscoveryRun(
        workspace_id=job.workspace_id,
        search_job_id=job.id,
        status="running",
        records_seen=0,
        leads_created=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    job.status = "running"
    db.flush()

    total_seen = 0
    total_created = 0
    total_duplicates = 0
    total_analyzed = 0
    errors = []
    source_results = []

    for link in links:
        source_id = link.search_source_id

        try:
            with db.begin_nested():
                source = db.get(SearchSource, source_id)
                if source is None:
                    raise ValueError("Linked SearchSource does not exist")
                if source.workspace_id != job.workspace_id:
                    raise ValueError("Linked SearchSource belongs to another workspace")

                context = ConnectorContext(
                    workspace_id=job.workspace_id,
                    query=job.query,
                    location=job.location or "",
                    config=dict(source.config_json),
                )

                collected = collect_from_search_source(
                    db=db,
                    source_id=source_id,
                    context=context,
                    registry=registry,
                    rate_limiter=rate_limiter,
                    max_records=max_records_per_source,
                )

                # Count records observed even if later persistence or analysis fails.
                total_seen += collected["records_seen"]

                persisted = persist_connector_records(
                    db=db,
                    records=collected["records"],
                    workspace_id=job.workspace_id,
                    search_source_id=source_id,
                    discovery_run_id=run.id,
                )

                analyzed = 0
                for record_id in persisted["created_source_record_ids"]:
                    analyze_source_record(
                        db=db,
                        source_record_id=record_id,
                        workspace_id=job.workspace_id,
                    )
                    analyzed += 1

                total_created += persisted["created"]
                total_duplicates += persisted["duplicates_skipped"]
                total_analyzed += analyzed

                source_results.append({
                    "source_id": source_id,
                    "status": "completed",
                    "records_seen": collected["records_seen"],
                    "records_created": persisted["created"],
                    "duplicates_skipped": persisted["duplicates_skipped"],
                    "records_analyzed": analyzed,
                })

        except Exception as exc:
            # Never persist raw exception messages; they may contain
            # credentials, internal paths, URLs, or source configuration.
            message = f"{type(exc).__name__}: source processing failed"
            errors.append(f"{source_id}: {message}")
            source_results.append({
                "source_id": source_id,
                "status": "failed",
                "error": message,
            })

    run.records_seen = total_seen
    run.error_summary = "\n".join(errors)[:4000] if errors else None
    run.finished_at = datetime.now(timezone.utc)

    if errors and (total_created or total_seen):
        run.status = "partial"
        job.status = "partial"
    elif errors:
        run.status = "failed"
        job.status = "failed"
    else:
        run.status = "completed"
        job.status = "completed"

    db.flush()

    return {
        "search_job_id": job.id,
        "discovery_run_id": run.id,
        "status": run.status,
        "records_seen": total_seen,
        "records_created": total_created,
        "duplicates_skipped": total_duplicates,
        "records_analyzed": total_analyzed,
        "leads_created": 0,
        "source_results": source_results,
        "error_summary": run.error_summary,
    }
