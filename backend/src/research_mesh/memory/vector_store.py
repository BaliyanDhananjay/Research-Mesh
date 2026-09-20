"""Chroma-backed semantic index for research evidence chunks.

The embedding function is always supplied explicitly by the caller so no
implicit network call or model download happens as a side effect of
constructing this adapter.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.api.types import Documents, Embeddings
from chromadb.api.types import EmbeddingFunction as ChromaEmbeddingFunction


class CallableEmbeddingFunction(ChromaEmbeddingFunction[Documents]):
    """Adapts a plain `list[str] -> list[list[float]]` callable to Chroma's interface."""

    def __init__(self, fn: Callable[[list[str]], list[list[float]]], *, name: str) -> None:
        self._fn = fn
        self._name = name

    def __call__(self, input: Documents) -> Embeddings:
        return self._fn(list(input))  # type: ignore[return-value]

    def name(self) -> str:  # type: ignore[override]  # per-instance name; base expects a class-level staticmethod
        return self._name


@dataclass(frozen=True)
class EvidenceMatch:
    source_id: str
    chunk_id: str
    text: str
    distance: float


class ChromaVectorStore:
    """In-process semantic index for evidence chunks, scoped per research run."""

    def __init__(
        self,
        *,
        embedding_function: ChromaEmbeddingFunction[Documents],
        persist_directory: str | None = None,
    ) -> None:
        client: Any = (
            chromadb.PersistentClient(path=persist_directory)
            if persist_directory
            else chromadb.EphemeralClient()
        )
        self._collection = client.get_or_create_collection(
            name="research_evidence",
            embedding_function=embedding_function,
        )

    def add_evidence(self, *, run_id: str, source_id: str, chunk_id: str, text: str) -> None:
        if not text.strip():
            raise ValueError("Evidence text cannot be empty")
        self._collection.add(
            ids=[chunk_id],
            documents=[text],
            metadatas=[{"run_id": run_id, "source_id": source_id}],
        )

    def query(self, *, run_id: str, text: str, top_k: int = 5) -> list[EvidenceMatch]:
        if not text.strip():
            raise ValueError("Query text cannot be empty")
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")

        results = self._collection.query(
            query_texts=[text],
            n_results=top_k,
            where={"run_id": run_id},
        )
        ids = results.get("ids") or [[]]
        documents = results.get("documents") or [[]]
        distances = results.get("distances") or [[]]
        metadatas = results.get("metadatas") or [[]]

        matches: list[EvidenceMatch] = []
        for index, chunk_id_value in enumerate(ids[0]):
            metadata = metadatas[0][index] or {}
            matches.append(
                EvidenceMatch(
                    source_id=str(metadata.get("source_id", "")),
                    chunk_id=str(chunk_id_value),
                    text=str(documents[0][index]),
                    distance=float(distances[0][index]),
                )
            )
        return matches
