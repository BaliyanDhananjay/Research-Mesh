"""Coordinates the end-to-end research pipeline across all agent roles."""

from typing import Protocol
from uuid import UUID

import httpx

from research_mesh.agents.parsing import parse_agent_response
from research_mesh.agents.schemas import DraftReport, ResearchPlan
from research_mesh.agents.validation import require_grounded_report
from research_mesh.domain.models import (
    Citation,
    Claim,
    Report,
    ResearchRequest,
    ResearchRun,
    RunEvent,
    RunStatus,
    SourceDocument,
)
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.memory.vector_store import ChromaVectorStore
from research_mesh.orchestration.indexing import index_source_document
from research_mesh.orchestration.model_client import ChatMessage
from research_mesh.orchestration.state import transition_status
from research_mesh.retrieval.extraction import content_hash, deduplicate_candidates, extract_text
from research_mesh.retrieval.extraction import extract_pdf_text as extract_pdf_text_from_bytes
from research_mesh.retrieval.fetch import FetchedDocument
from research_mesh.retrieval.models import SourceCandidate
from research_mesh.retrieval.quality import score_source


class SearchProvider(Protocol):
    def search(self, query: str, *, limit: int = 10) -> list[SourceCandidate]: ...


class Fetcher(Protocol):
    def fetch(self, url: str) -> FetchedDocument: ...


class ChatClient(Protocol):
    def complete(self, messages: list[ChatMessage], *, as_json: bool = False) -> str: ...


class ResearchRunFailed(RuntimeError):
    """Raised when a run fails; carries the run id so callers can inspect it."""

    def __init__(self, run_id: UUID, message: str) -> None:
        super().__init__(message)
        self.run_id = run_id


PLANNER_SYSTEM_PROMPT = (
    "You are a research planner. Given a question, return JSON with a "
    '"search_queries" list of 2-5 focused web search queries.'
)

SYNTHESIZER_SYSTEM_PROMPT = (
    "You are a research report writer. Using only the provided evidence chunks, "
    "return JSON with title, summary, claims (each with text, supporting_chunk_ids "
    "drawn only from the given chunk ids, and confidence), and limitations. "
    "Every claim must cite at least one supporting_chunk_id."
)


class ResearchOrchestrator:
    """Runs the plan -> search -> index -> synthesize pipeline for one request."""

    def __init__(
        self,
        *,
        repository: SQLiteRepository,
        vector_store: ChromaVectorStore,
        search_provider: SearchProvider,
        fetcher: Fetcher,
        chat_client: ChatClient,
        max_sources: int = 5,
    ) -> None:
        self._repository = repository
        self._vector_store = vector_store
        self._search_provider = search_provider
        self._fetcher = fetcher
        self._chat_client = chat_client
        self._max_sources = max_sources

    def run(self, request: ResearchRequest) -> Report:
        run = ResearchRun(request=request)
        self._repository.save_run(run)
        self._emit(run.id, "run.created", "Research run queued")

        try:
            self._transition(run, RunStatus.RUNNING)
            self._emit(run.id, "run.started", "Research run started")

            plan = self._plan(request)
            self._emit(run.id, "plan.created", f"Planned {len(plan.search_queries)} search queries")

            sources = self._search_and_index(run, plan)
            self._emit(run.id, "sources.indexed", f"Indexed {len(sources)} sources")

            known_chunk_ids = {chunk_id for _, chunk_ids in sources for chunk_id in chunk_ids}
            draft = self._synthesize(request, run)
            require_grounded_report(draft, known_chunk_ids)

            report = self._to_report(run.id, draft, sources)
            self._repository.save_report(report)
            self._emit(run.id, "report.created", "Report generated")

            self._transition(run, RunStatus.COMPLETED)
            return report
        except Exception as error:
            # Any pipeline stage failure marks the run FAILED and surfaces the run id.
            self._transition(run, RunStatus.FAILED, error=str(error))
            self._emit(run.id, "run.failed", str(error))
            raise ResearchRunFailed(run.id, str(error)) from error

    def _transition(self, run: ResearchRun, status: RunStatus, *, error: str | None = None) -> None:
        transition_status(run.status, status)
        run.status = status
        self._repository.update_status(str(run.id), status, error=error)

    def _emit(self, run_id: UUID, event_type: str, message: str) -> None:
        self._repository.add_event(RunEvent(run_id=run_id, event_type=event_type, message=message))

    def _plan(self, request: ResearchRequest) -> ResearchPlan:
        raw = self._chat_client.complete(
            [
                ChatMessage(role="system", content=PLANNER_SYSTEM_PROMPT),
                ChatMessage(role="user", content=request.question),
            ],
            as_json=True,
        )
        return parse_agent_response(raw, ResearchPlan)

    def _search_and_index(
        self, run: ResearchRun, plan: ResearchPlan
    ) -> list[tuple[SourceDocument, list[str]]]:
        candidates: list[SourceCandidate] = []
        for query in plan.search_queries:
            candidates.extend(self._search_provider.search(query, limit=10))

        unique = deduplicate_candidates(candidates)
        scored = sorted(unique, key=score_source, reverse=True)[: self._max_sources]

        indexed: list[tuple[SourceDocument, list[str]]] = []
        for candidate in scored:
            try:
                document = self._fetcher.fetch(str(candidate.url))
            except (ValueError, httpx.HTTPError):
                continue

            try:
                if document.content_type == "application/pdf":
                    extracted = extract_pdf_text_from_bytes(document.content_bytes)
                else:
                    extracted = extract_text(document.content, content_type=document.content_type)
            except ValueError:
                continue
            if not extracted:
                continue

            source = SourceDocument(
                run_id=run.id,
                url=candidate.url,
                title=candidate.title,
                source_type=candidate.source_type,
                domain=candidate.domain,
                quality_score=score_source(candidate),
                content_hash=content_hash(extracted),
            )
            self._repository.save_source(source)
            snippets = index_source_document(
                repository=self._repository,
                vector_store=self._vector_store,
                source=source,
                text=extracted,
            )
            indexed.append((source, [str(snippet.id) for snippet in snippets]))
        return indexed

    def _synthesize(self, request: ResearchRequest, run: ResearchRun) -> DraftReport:
        matches = self._vector_store.query(run_id=str(run.id), text=request.question, top_k=10)
        evidence_block = "\n".join(f"[{match.chunk_id}] {match.text}" for match in matches)
        if not evidence_block:
            evidence_block = "No evidence was retrieved."

        raw = self._chat_client.complete(
            [
                ChatMessage(role="system", content=SYNTHESIZER_SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=f"Question: {request.question}\n\nEvidence chunks:\n{evidence_block}",
                ),
            ],
            as_json=True,
        )
        return parse_agent_response(raw, DraftReport)

    def _to_report(
        self,
        run_id: UUID,
        draft: DraftReport,
        sources: list[tuple[SourceDocument, list[str]]],
    ) -> Report:
        chunk_to_source: dict[str, UUID] = {
            chunk_id: source.id for source, chunk_ids in sources for chunk_id in chunk_ids
        }
        claims: list[Claim] = []
        citations: list[Citation] = []
        for draft_claim in draft.claims:
            claim = Claim(
                text=draft_claim.text,
                evidence_ids=[UUID(chunk_id) for chunk_id in draft_claim.supporting_chunk_ids],
                confidence=draft_claim.confidence,
            )
            claims.append(claim)
            for chunk_id in draft_claim.supporting_chunk_ids:
                source_id = chunk_to_source.get(chunk_id)
                if source_id is not None:
                    citations.append(Citation(claim_id=claim.id, source_id=source_id))

        return Report(
            run_id=run_id,
            title=draft.title,
            summary=draft.summary,
            claims=claims,
            citations=citations,
            limitations=draft.limitations,
        )
