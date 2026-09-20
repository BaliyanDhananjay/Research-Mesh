import hashlib
from uuid import UUID

import pytest
from research_mesh.domain.models import ResearchRequest, ResearchRun, SourceDocument
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.memory.vector_store import CallableEmbeddingFunction, ChromaVectorStore
from research_mesh.orchestration.indexing import index_source_document

_DIMENSIONS = 16


def _hash_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic, non-semantic embedding used only to test pipeline plumbing."""
    embeddings = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        embeddings.append([digest[i % len(digest)] / 255 for i in range(_DIMENSIONS)])
    return embeddings


def _make_source(run_id: UUID) -> SourceDocument:
    return SourceDocument(
        run_id=run_id,
        url="https://www.who.int/coral-bleaching",
        title="Coral bleaching overview",
        source_type="official",
        domain="who.int",
        quality_score=0.8,
    )


def test_index_source_document_persists_and_indexes_chunks() -> None:
    repository = SQLiteRepository(":memory:")
    run = ResearchRun(request=ResearchRequest(question="What causes coral bleaching?"))
    repository.save_run(run)
    source = _make_source(run.id)
    repository.save_source(source)
    vector_store = ChromaVectorStore(
        embedding_function=CallableEmbeddingFunction(_hash_embed, name="test-hash-embedding")
    )

    snippets = index_source_document(
        repository=repository,
        vector_store=vector_store,
        source=source,
        text="Warmer oceans stress coral. " * 40,
        max_chunk_chars=100,
    )

    assert len(snippets) > 1
    stored = repository.list_evidence_for_source(str(source.id))
    assert stored == snippets

    matches = vector_store.query(run_id=str(run.id), text=snippets[0].text, top_k=5)
    assert any(match.chunk_id == str(snippets[0].id) for match in matches)


def test_index_source_document_rejects_empty_text() -> None:
    repository = SQLiteRepository(":memory:")
    run = ResearchRun(request=ResearchRequest(question="What causes coral bleaching?"))
    repository.save_run(run)
    source = _make_source(run.id)
    repository.save_source(source)
    vector_store = ChromaVectorStore(
        embedding_function=CallableEmbeddingFunction(_hash_embed, name="test-hash-embedding")
    )

    with pytest.raises(ValueError):
        index_source_document(
            repository=repository, vector_store=vector_store, source=source, text="   "
        )
