"""Common interface and validated data contract for source connectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit


@dataclass(frozen=True)
class ConnectorContext:
    workspace_id: str
    query: str
    location: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    fetcher: Callable[[str], dict] | None = field(
        default=None, compare=False, repr=False
    )

    def __post_init__(self):
        if not isinstance(self.workspace_id, str) or not self.workspace_id.strip():
            raise ValueError("workspace_id must be a non-empty string")
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(self.location, str):
            raise TypeError("location must be a string")
        if not isinstance(self.config, dict):
            raise TypeError("config must be a dictionary")


@dataclass(frozen=True)
class ConnectorRecord:
    source_url: str
    title: str | None = None
    excerpt: str | None = None
    external_id: str | None = None
    published_at: datetime | None = None
    attribution: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.source_url, str):
            raise TypeError("source_url must be a string")

        parsed = urlsplit(self.source_url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be a valid HTTP or HTTPS URL")

        if self.title is not None:
            if not isinstance(self.title, str) or len(self.title) > 500:
                raise ValueError("title must be a string of at most 500 characters")

        if self.excerpt is not None:
            if not isinstance(self.excerpt, str) or len(self.excerpt) > 20000:
                raise ValueError("excerpt must be a string of at most 20000 characters")

        if self.external_id is not None:
            if not isinstance(self.external_id, str) or len(self.external_id) > 250:
                raise ValueError("external_id must be a string of at most 250 characters")

        if self.attribution is not None:
            if not isinstance(self.attribution, str) or len(self.attribution) > 500:
                raise ValueError("attribution must be a string of at most 500 characters")

        if self.published_at is not None and not isinstance(self.published_at, datetime):
            raise TypeError("published_at must be a datetime or None")

        if not isinstance(self.raw_data, dict):
            raise TypeError("raw_data must be a dictionary")


class SourceConnector(ABC):
    """Base class for connectors that do not require network transport."""

    connector_key: str
    source_type: str

    @abstractmethod
    def collect(self, context: ConnectorContext) -> Iterable[ConnectorRecord]:
        raise NotImplementedError


class ControlledNetworkConnector(SourceConnector):
    """Connector that must use the workspace-approved context.fetcher.

    This is an application contract, not an OS-level network sandbox.
    Implementations must not open their own network connections.
    """

    @abstractmethod
    def collect(self, context: ConnectorContext) -> Iterable[ConnectorRecord]:
        if context.fetcher is None:
            raise RuntimeError("Controlled network fetcher is unavailable")
        raise NotImplementedError
