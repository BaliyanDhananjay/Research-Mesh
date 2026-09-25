import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from research_mesh.api.app import app
from research_mesh.api.dependencies import get_job_manager, get_orchestrator, get_repository
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.memory.vector_store import CallableEmbeddingFunction, ChromaVectorStore
from research_mesh.orchestration.model_client import ChatMessage
from research_mesh.orchestration.runner import ResearchOrchestrator
from research_mesh.retrieval.fetch import FetchedDocument
from research_mesh.retrieval.models import SourceCandidate

_DIMENSIONS = 16


def _hash_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic, non-semantic embedding used only to test API plumbing."""
    embeddings = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        embeddings.append([digest[i % len(digest)] / 255 for i in range(_DIMENSIONS)])
    return embeddings


class _FakeSearchProvider:
    def __init__(self, candidates: list[SourceCandidate]) -> None:
        self._candidates = candidates

    def search(self, query: str, *, limit: int = 10) -> list[SourceCandidate]:
        return self._candidates[:limit]


class _FakeFetcher:
    def __init__(self, documents: dict[str, FetchedDocument]) -> None:
        self._documents = documents

    def fetch(self, url: str) -> FetchedDocument:
        return self._documents[url]


class _FakeChatClient:
    """Returns a canned plan, then a synthesis grounded in whatever chunk id it was given."""

    def __init__(self, plan_response: str) -> None:
        self._plan_response = plan_response
        self.calls: list[list[ChatMessage]] = []

    def complete(self, messages: list[ChatMessage], *, as_json: bool = False) -> str:
        self.calls.append(messages)
        if len(self.calls) == 1:
            return self._plan_response

        evidence_message = messages[-1].content
        chunk_id = evidence_message.split("[", 1)[1].split("]", 1)[0]
        return json.dumps(
            {
                "title": "Coral Bleaching Summary",
                "summary": "Warmer oceans stress coral reefs.",
                "claims": [
                    {
                        "text": "Warmer oceans stress coral reefs.",
                        "supporting_chunk_ids": [chunk_id],
                        "confidence": 0.9,
                    }
                ],
                "limitations": ["Single source reviewed."],
            }
        )


class _SyncJobManager:
    """Runs submitted tasks immediately, so API tests don't need to poll."""

    def submit(self, run_id: UUID, task: object) -> None:
        task()  # type: ignore[operator]


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    database_path = str(tmp_path / "test.sqlite3")
    repository = SQLiteRepository(database_path)
    vector_store = ChromaVectorStore(
        embedding_function=CallableEmbeddingFunction(_hash_embed, name="test-hash-embedding"),
        persist_directory=str(tmp_path / "chroma"),
    )
    candidate = SourceCandidate(
        url="https://example.com/coral",
        title="Coral bleaching study",
        source_type="official",
        domain="example.com",
    )
    fetcher = _FakeFetcher(
        {
            "https://example.com/coral": FetchedDocument(
                url="https://example.com/coral",
                content_type="text/html",
                content="<p>Warmer oceans stress coral reefs significantly.</p>",
            )
        }
    )
    orchestrator = ResearchOrchestrator(
        repository=repository,
        vector_store=vector_store,
        search_provider=_FakeSearchProvider([candidate]),
        fetcher=fetcher,
        chat_client=_FakeChatClient('{"search_queries": ["coral bleaching causes"]}'),
    )

    def _get_repository() -> Iterator[SQLiteRepository]:
        request_repository = SQLiteRepository(database_path)
        try:
            yield request_repository
        finally:
            request_repository.close()

    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_job_manager] = lambda: _SyncJobManager()
    app.dependency_overrides[get_repository] = _get_repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    repository.close()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_retrieve_a_completed_run(client: TestClient) -> None:
    response = client.post("/runs", json={"question": "What causes coral bleaching?"})

    assert response.status_code == 202
    run_id = response.json()["id"]

    run_response = client.get(f"/runs/{run_id}")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "completed"

    events_response = client.get(f"/runs/{run_id}/events")
    assert events_response.status_code == 200
    assert len(events_response.json()) > 0

    sources_response = client.get(f"/runs/{run_id}/sources")
    assert sources_response.status_code == 200
    assert len(sources_response.json()) == 1

    report_response = client.get(f"/runs/{run_id}/report")
    assert report_response.status_code == 200
    assert report_response.json()["title"] == "Coral Bleaching Summary"


def test_get_run_returns_404_for_unknown_run(client: TestClient) -> None:
    response = client.get("/runs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_report_returns_404_before_run_exists(client: TestClient) -> None:
    response = client.get("/runs/00000000-0000-0000-0000-000000000000/report")

    assert response.status_code == 404
