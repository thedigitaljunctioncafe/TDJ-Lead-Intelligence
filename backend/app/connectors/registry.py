"""In-memory registry for available source connectors."""

import re
from .base import SourceConnector


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, SourceConnector] = {}

    def register(self, connector: SourceConnector) -> None:
        if not isinstance(connector, SourceConnector):
            raise TypeError("connector must inherit from SourceConnector")

        key = getattr(connector, "connector_key", None)
        source_type = getattr(connector, "source_type", None)

        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,99}", key):
            raise ValueError("connector_key must be a valid lowercase identifier")

        if not isinstance(source_type, str) or not source_type.strip():
            raise ValueError("source_type must be a non-empty string")

        if key in self._connectors:
            raise ValueError(f"Connector already registered: {key}")

        self._connectors[key] = connector

    def get(self, key: str) -> SourceConnector:
        try:
            return self._connectors[key]
        except KeyError:
            raise KeyError(f"Connector not registered: {key}") from None

    def list_keys(self) -> list[str]:
        return sorted(self._connectors.keys())

    def unregister(self, key: str) -> bool:
        return self._connectors.pop(key, None) is not None
