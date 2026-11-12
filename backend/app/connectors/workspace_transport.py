"""Workspace-authorized HTTPS transport for configured public feeds."""

from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain_allowlist_service import normalize_domain
from app.models import SearchSource, Workspace, WorkspaceDomainAllowlist
from .pinned_https import request_public_https


def request_search_source_https(
    db: Session,
    source_id: str,
    url: str,
    *,
    resolver=None,
    timeout=10,
    max_response_bytes=2_000_000,
) -> dict:
    """Fetch only a source's exact configured feed URL on an active approved domain.

    The caller owns the SQLAlchemy transaction. Redirects are not followed.
    """
    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")

    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id is required")

    if not isinstance(url, str) or not url.strip():
        raise ValueError("A feed URL is required")

    source = db.get(SearchSource, source_id)
    if source is None:
        raise ValueError("SearchSource does not exist")

    if not source.enabled:
        raise ValueError("SearchSource is disabled")

    if source.access_policy != "public_only":
        raise ValueError("Only public_only sources are permitted")

    if source.source_type not in {"rss", "atom"}:
        raise ValueError("Only RSS and Atom sources are permitted")

    if not isinstance(source.config_json, dict):
        raise ValueError("SearchSource config_json must be a dictionary")

    configured_url = source.config_json.get("feed_url")
    if not isinstance(configured_url, str) or not configured_url.strip():
        raise ValueError("SearchSource must have a configured feed_url")

    requested_url = url.strip()
    if requested_url != configured_url.strip():
        raise ValueError("Requested URL does not match the configured feed_url")

    workspace = db.get(Workspace, source.workspace_id)
    if workspace is None or not workspace.is_active:
        raise ValueError("Source workspace does not exist or is inactive")

    try:
        parsed = urlsplit(requested_url)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError("Malformed feed URL") from exc

    if not hostname:
        raise ValueError("Feed URL hostname is required")

    domain = normalize_domain(hostname)

    approved_domains = list(
        db.scalars(
            select(WorkspaceDomainAllowlist.domain).where(
                WorkspaceDomainAllowlist.workspace_id == source.workspace_id,
                WorkspaceDomainAllowlist.is_active.is_(True),
            )
        ).all()
    )

    if domain not in approved_domains:
        raise ValueError("Feed domain is not actively approved for this workspace")

    return request_public_https(
        requested_url,
        approved_domains,
        resolver=resolver,
        timeout=timeout,
        max_response_bytes=max_response_bytes,
    )
