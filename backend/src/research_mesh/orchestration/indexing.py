"""Bridges extracted evidence text into persistent storage and the semantic index."""

from research_mesh.domain.models import EvidenceSnippet, SourceDocument
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.memory.vector_store import ChromaVectorStore
from research_mesh.retrieval.extraction import chunk_text


def index_source_document(
    *,
    repository: SQLiteRepository,
    vector_store: ChromaVectorStore,
    source: SourceDocument,
    text: str,
    max_chunk_chars: int = 800,
) -> list[EvidenceSnippet]:
    """Chunk source text, persist it as evidence, and index it for semantic search."""
    chunks = chunk_text(text, max_chars=max_chunk_chars)
    if not chunks:
        raise ValueError("No evidence chunks were produced from the source text")

    snippets: list[EvidenceSnippet] = []
    for position, chunk in enumerate(chunks):
        snippet = EvidenceSnippet(source_id=source.id, text=chunk, locator=f"chunk-{position}")
        repository.save_evidence(snippet)
        vector_store.add_evidence(
            run_id=str(source.run_id),
            source_id=str(source.id),
            chunk_id=str(snippet.id),
            text=chunk,
        )
        snippets.append(snippet)
    return snippets
