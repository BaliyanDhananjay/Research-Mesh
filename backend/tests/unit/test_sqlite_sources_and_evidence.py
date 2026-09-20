from research_mesh.domain.models import (
    EvidenceSnippet,
    ResearchRequest,
    ResearchRun,
    SourceDocument,
)
from research_mesh.memory.sqlite import SQLiteRepository


def test_sources_and_evidence_persist_and_list_for_a_run() -> None:
    repository = SQLiteRepository(":memory:")
    run = ResearchRun(request=ResearchRequest(question="What causes coral bleaching?"))
    repository.save_run(run)

    source = SourceDocument(
        run_id=run.id,
        url="https://www.who.int/coral-bleaching",
        title="Coral bleaching overview",
        source_type="official",
        domain="who.int",
        quality_score=0.8,
        content_hash="abc123",
    )
    repository.save_source(source)
    evidence = EvidenceSnippet(
        source_id=source.id,
        text="Warmer oceans stress coral.",
        locator="p1",
    )
    repository.save_evidence(evidence)

    sources = repository.list_sources_for_run(str(run.id))
    stored_evidence = repository.list_evidence_for_source(str(source.id))

    assert sources == [source]
    assert stored_evidence == [evidence]


def test_sources_for_unknown_run_returns_empty_list() -> None:
    repository = SQLiteRepository(":memory:")

    assert repository.list_sources_for_run("11111111-1111-1111-1111-111111111111") == []
