"""Safe integration between database SearchSource rows and connectors."""

from dataclasses import replace
from itertools import islice

from sqlalchemy.orm import Session

from ..models import SearchSource
from .base import (
    ConnectorContext,
    ConnectorRecord,
    ControlledNetworkConnector,
)
from .rate_limit import RateLimiter
from .registry import ConnectorRegistry


def collect_from_search_source(
    db: Session,
    source_id: str,
    context: ConnectorContext,
    registry: ConnectorRegistry,
    rate_limiter: RateLimiter,
    max_records: int = 50,
) -> dict:
    """Collect bounded records from one enabled, public-only registered source.

    This function does not persist records or commit/rollback the transaction.
    The connector implementation is responsible for lawful network access.
    """

    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")

    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")

    if not isinstance(context, ConnectorContext):
        raise TypeError("context must be a ConnectorContext")

    if not isinstance(registry, ConnectorRegistry):
        raise TypeError("registry must be a ConnectorRegistry")

    if not isinstance(rate_limiter, RateLimiter):
        raise TypeError("rate_limiter must be a RateLimiter")

    if isinstance(max_records, bool) or not isinstance(max_records, int):
        raise TypeError("max_records must be an integer")

    if not 1 <= max_records <= 500:
        raise ValueError("max_records must be between 1 and 500")

    source = db.get(SearchSource, source_id)

    if source is None:
        raise ValueError("SearchSource does not exist")

    if source.workspace_id != context.workspace_id:
        raise ValueError("SearchSource belongs to a different workspace")

    if not source.enabled:
        raise ValueError("SearchSource is disabled")

    if source.access_policy != "public_only":
        raise ValueError("Only public_only sources are permitted")

    if not isinstance(source.config_json, dict):
        raise ValueError("SearchSource config_json must be a dictionary")

    connector = registry.get(source.source_key)

    if connector.source_type != source.source_type:
        raise ValueError("Connector source_type does not match SearchSource")

    if isinstance(connector, ControlledNetworkConnector):
        if source.source_type not in {"rss", "atom"}:
            raise ValueError(
                "Controlled network connectors support only RSS and Atom sources"
            )

        feed_url = source.config_json.get("feed_url")
        if not isinstance(feed_url, str) or not feed_url.strip():
            raise ValueError(
                "Controlled network source requires a configured feed_url"
            )

        from .workspace_transport import request_search_source_https

        def approved_fetcher(requested_url: str) -> dict:
            return request_search_source_https(
                db=db,
                source_id=source.id,
                url=requested_url,
            )

        context = replace(context, fetcher=approved_fetcher)
    elif context.fetcher is not None:
        raise ValueError(
            "A custom fetcher cannot be supplied to an uncontrolled connector"
        )

    if not isinstance(connector, ControlledNetworkConnector):
        if source.source_type != "mock":
            raise ValueError(
                "Uncontrolled connectors are permitted only for mock sources"
            )

    rate_limiter.acquire(source.source_key)

    collected = connector.collect(context)

    if collected is None:
        raise ValueError("Connector returned no iterable")

    try:
        iterator = iter(collected)
    except TypeError:
        raise TypeError("Connector must return an iterable of ConnectorRecord") from None

    records = list(islice(iterator, max_records))

    if not all(isinstance(record, ConnectorRecord) for record in records):
        raise TypeError("Connector returned an invalid record")

    return {
        "source_id": source.id,
        "source_key": source.source_key,
        "source_type": source.source_type,
        "workspace_id": source.workspace_id,
        "records_seen": len(records),
        "records": records,
    }
