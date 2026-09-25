import pytest

from research_mesh.agents.schemas import DraftClaim, DraftReport
from research_mesh.agents.validation import find_ungrounded_claims, require_grounded_report


def _report(*, supporting_chunk_ids: list[str]) -> DraftReport:
    return DraftReport(
        title="Coral bleaching",
        summary="Warmer oceans stress coral reefs.",
        claims=[
            DraftClaim(
                text="Warmer oceans stress coral.", supporting_chunk_ids=supporting_chunk_ids
            )
        ],
    )


def test_claim_with_known_chunk_id_is_grounded() -> None:
    report = _report(supporting_chunk_ids=["chunk-1"])

    assert find_ungrounded_claims(report, known_chunk_ids={"chunk-1"}) == []
    require_grounded_report(report, known_chunk_ids={"chunk-1"})


def test_claim_without_any_supporting_chunks_is_rejected() -> None:
    report = _report(supporting_chunk_ids=[])

    ungrounded = find_ungrounded_claims(report, known_chunk_ids={"chunk-1"})

    assert ungrounded == ["Warmer oceans stress coral."]
    with pytest.raises(ValueError, match="without valid supporting evidence"):
        require_grounded_report(report, known_chunk_ids={"chunk-1"})


def test_claim_citing_unknown_chunk_id_is_rejected() -> None:
    report = _report(supporting_chunk_ids=["chunk-does-not-exist"])

    with pytest.raises(ValueError, match="without valid supporting evidence"):
        require_grounded_report(report, known_chunk_ids={"chunk-1"})
