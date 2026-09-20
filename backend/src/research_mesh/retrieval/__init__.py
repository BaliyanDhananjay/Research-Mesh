"""Source discovery and evidence acquisition boundaries."""

from research_mesh.retrieval.extraction import (
    canonicalize_url,
    chunk_text,
    content_hash,
    deduplicate_candidates,
    extract_pdf_text,
    extract_text,
)
from research_mesh.retrieval.fetch import FetchedDocument, SourceFetcher
from research_mesh.retrieval.quality import score_source
from research_mesh.retrieval.safety import validate_fetch_url

__all__ = [
    "canonicalize_url",
    "chunk_text",
    "content_hash",
    "deduplicate_candidates",
    "extract_pdf_text",
    "extract_text",
    "FetchedDocument",
    "score_source",
    "SourceFetcher",
    "validate_fetch_url",
]
