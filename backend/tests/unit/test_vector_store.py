import hashlib
from pathlib import Path

import pytest
from research_mesh.memory.vector_store import CallableEmbeddingFunction, ChromaVectorStore

_DIMENSIONS = 16


def _hash_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic, non-semantic embedding used only to test adapter behavior."""
    embeddings = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        embeddings.append([digest[i % len(digest)] / 255 for i in range(_DIMENSIONS)])
    return embeddings


def _test_embedding_function() -> CallableEmbeddingFunction:
    return CallableEmbeddingFunction(_hash_embed, name="test-hash-embedding")


def test_query_is_scoped_to_the_requesting_run(tmp_path: Path) -> None:
    store = ChromaVectorStore(
        embedding_function=_test_embedding_function(), persist_directory=str(tmp_path)
    )

    store.add_evidence(
        run_id="run-a", source_id="source-1", chunk_id="chunk-1", text="Coral reefs are bleaching."
    )
    store.add_evidence(
        run_id="run-b", source_id="source-2", chunk_id="chunk-2", text="Coral reefs are bleaching."
    )

    results = store.query(run_id="run-a", text="Coral reefs are bleaching.", top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].source_id == "source-1"


def test_add_evidence_rejects_empty_text(tmp_path: Path) -> None:
    store = ChromaVectorStore(
        embedding_function=_test_embedding_function(), persist_directory=str(tmp_path)
    )

    with pytest.raises(ValueError):
        store.add_evidence(run_id="run-a", source_id="source-1", chunk_id="chunk-1", text="   ")


def test_query_rejects_invalid_top_k(tmp_path: Path) -> None:
    store = ChromaVectorStore(
        embedding_function=_test_embedding_function(), persist_directory=str(tmp_path)
    )
    store.add_evidence(run_id="run-a", source_id="source-1", chunk_id="chunk-1", text="Evidence")

    with pytest.raises(ValueError):
        store.query(run_id="run-a", text="Evidence", top_k=0)
