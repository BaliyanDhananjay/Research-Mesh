"""Safe, bounded retrieval of source text before extraction."""

from dataclasses import dataclass

import httpx

from research_mesh.retrieval.safety import validate_fetch_url

_TEXT_CONTENT_TYPES = {"text/html", "text/plain"}
_SUPPORTED_CONTENT_TYPES = _TEXT_CONTENT_TYPES | {"application/pdf"}


@dataclass(frozen=True)
class FetchedDocument:
    url: str
    content_type: str
    content: str = ""
    content_bytes: bytes = b""


class SourceFetcher:
    def __init__(self, *, client: httpx.Client | None = None, max_bytes: int = 2_000_000) -> None:
        if max_bytes < 1_024:
            raise ValueError("max_bytes must be at least 1024")
        self._client = client or httpx.Client(timeout=10.0, follow_redirects=False)
        self._owns_client = client is None
        self.max_bytes = max_bytes

    def fetch(self, url: str) -> FetchedDocument:
        validate_fetch_url(url)
        response = self._client.get(url, follow_redirects=False)
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError("Redirects must be resolved and validated by the caller")
        if len(response.content) > self.max_bytes:
            raise ValueError("Response exceeds the configured size limit")
        content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
        if content_type not in _SUPPORTED_CONTENT_TYPES:
            raise ValueError(f"Unsupported content type: {content_type or 'unknown'}")
        is_text = content_type in _TEXT_CONTENT_TYPES
        return FetchedDocument(
            url=str(response.url),
            content_type=content_type,
            content=response.text if is_text else "",
            content_bytes=b"" if is_text else response.content,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
