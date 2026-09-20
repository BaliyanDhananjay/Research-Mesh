"""Search provider interface and SearXNG-compatible implementation."""

from collections.abc import Mapping
from typing import Protocol

import httpx

from research_mesh.retrieval.models import SourceCandidate
from research_mesh.retrieval.safety import validate_fetch_url


class SearchProvider(Protocol):
    def search(self, query: str, *, limit: int = 10) -> list[SourceCandidate]: ...


class SearXNGSearchProvider:
    def __init__(
        self,
        endpoint: str,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        validate_fetch_url(endpoint)
        self.endpoint = endpoint
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._owns_client = client is None

    def search(self, query: str, *, limit: int = 10) -> list[SourceCandidate]:
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if not 1 <= limit <= 50:
            raise ValueError("Search limit must be between 1 and 50")

        response = self._client.get(
            self.endpoint,
            params={"q": query, "format": "json", "categories": "general"},
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, Mapping) else []
        candidates: list[SourceCandidate] = []
        for result in results[:limit]:
            if not isinstance(result, Mapping) or not result.get("url"):
                continue
            try:
                candidates.append(
                    SourceCandidate(
                        url=result["url"],
                        title=str(result.get("title", "")),
                        snippet=str(result.get("content", "")),
                    )
                )
            except (TypeError, ValueError):
                continue
        return candidates

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
