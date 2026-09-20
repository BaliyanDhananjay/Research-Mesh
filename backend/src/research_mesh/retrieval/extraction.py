"""Convert fetched source content into normalized, citeable evidence."""

import hashlib
import re
from collections.abc import Iterable
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from research_mesh.retrieval.models import SourceCandidate


class _TextExtractor(HTMLParser):
    _IGNORED_TAGS = {"script", "style", "noscript", "template", "svg"}
    _BLOCK_TAGS = {"article", "br", "div", "h1", "h2", "h3", "li", "p", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._IGNORED_TAGS:
            self._ignored_depth += 1
        elif self._ignored_depth == 0 and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORED_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1
        elif self._ignored_depth == 0 and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)


def canonicalize_url(url: str) -> str:
    """Normalize a URL for duplicate detection while preserving its meaningful path."""
    parts = urlsplit(url.strip())
    tracking_prefixes = ("utm_", "mc_", "ref")
    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith(tracking_prefixes)
    ]
    query = urlencode(sorted(query_items))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", query, ""))


def content_hash(text: str) -> str:
    normalized = normalize_text(text).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def extract_text(content: str, *, content_type: str = "text/html") -> str:
    """Extract readable text from HTML; plain text is normalized directly."""
    if "html" in content_type.lower():
        parser = _TextExtractor()
        parser.feed(content)
        content = "".join(parser.parts)
    return normalize_text(content)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, *, max_chars: int = 800) -> list[str]:
    """Create bounded chunks without splitting words or emitting empty evidence."""
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    words = normalize_text(text).split()
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for word in words:
        proposed_length = current_length + len(word) + (1 if current else 0)
        if current and proposed_length > max_chars:
            chunks.append(" ".join(current))
            current = []
            current_length = 0
        current.append(word)
        current_length += len(word) + (1 if current_length else 0)
    if current:
        chunks.append(" ".join(current))
    return chunks


def deduplicate_candidates(candidates: Iterable[SourceCandidate]) -> list[SourceCandidate]:
    """Keep the first result for each canonical URL."""
    unique: list[SourceCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = canonicalize_url(str(candidate.url))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique
