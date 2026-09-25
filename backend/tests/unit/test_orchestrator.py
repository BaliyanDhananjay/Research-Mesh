import hashlib
import json
from pathlib import Path

import pytest

from research_mesh.domain.models import ResearchRequest, RunStatus
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.memory.vector_store import CallableEmbeddingFunction, ChromaVectorStore
from research_mesh.orchestration.model_client import ChatMessage
from research_mesh.orchestration.runner import ResearchOrchestrator, ResearchRunFailed
from research_mesh.retrieval.fetch import FetchedDocument
from research_mesh.retrieval.models import SourceCandidate

_DIMENSIONS = 16


def _hash_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic, non-semantic embedding used only to test pipeline plumbing."""
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

    def __init__(self, plan_response: str, *, grounded: bool = True) -> None:
        self._plan_response = plan_response
        self._grounded = grounded
        self.calls: list[list[ChatMessage]] = []

    def complete(self, messages: list[ChatMessage], *, as_json: bool = False) -> str:
        self.calls.append(messages)
        if len(self.calls) == 1:
            return self._plan_response

        supporting_chunk_ids: list[str] = []
        if self._grounded:
            evidence_message = messages[-1].content
            chunk_id = evidence_message.split("[", 1)[1].split("]", 1)[0]
            supporting_chunk_ids = [chunk_id]

        return json.dumps(
            {
                "title": "Coral Bleaching Summary",
                "summary": "Warmer oceans stress coral reefs.",
                "claims": [
                    {
                        "text": "Warmer oceans stress coral reefs.",
                        "supporting_chunk_ids": supporting_chunk_ids,
                        "confidence": 0.9,
                    }
                ],
                "limitations": ["Single source reviewed."],
            }
        )


def _build_orchestrator(
    chat_client: _FakeChatClient, tmp_path: Path
) -> tuple[ResearchOrchestrator, SQLiteRepository]:
    repository = SQLiteRepository(":memory:")
    vector_store = ChromaVectorStore(
        embedding_function=CallableEmbeddingFunction(_hash_embed, name="test-hash-embedding"),
        persist_directory=str(tmp_path),
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
        chat_client=chat_client,
    )
    return orchestrator, repository


def test_orchestrator_runs_full_pipeline_and_persists_a_grounded_report(tmp_path: Path) -> None:
    chat_client = _FakeChatClient('{"search_queries": ["coral bleaching causes"]}')
    orchestrator, repository = _build_orchestrator(chat_client, tmp_path)
    request = ResearchRequest(question="What causes coral bleaching?")

    report = orchestrator.run(request)

    assert report.title == "Coral Bleaching Summary"
    assert len(report.claims) == 1
    assert len(report.citations) == 1

    stored_report = repository.get_report_for_run(str(report.run_id))
    assert stored_report == report

    run = repository.get_run(str(report.run_id))
    assert run is not None
    assert run.status is RunStatus.COMPLETED


def test_orchestrator_marks_run_failed_when_report_is_not_grounded(tmp_path: Path) -> None:
    chat_client = _FakeChatClient('{"search_queries": ["coral bleaching causes"]}', grounded=False)
    orchestrator, repository = _build_orchestrator(chat_client, tmp_path)
    request = ResearchRequest(question="What causes coral bleaching?")

    with pytest.raises(ResearchRunFailed) as exc_info:
        orchestrator.run(request)

    run = repository.get_run(str(exc_info.value.run_id))
    assert run is not None
    assert run.status is RunStatus.FAILED
    assert run.error is not None
    assert "without valid supporting evidence" in run.error
