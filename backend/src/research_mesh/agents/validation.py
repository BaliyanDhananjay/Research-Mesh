"""Reject claims that are not grounded in retrieved evidence chunks."""

from research_mesh.agents.schemas import DraftReport


def find_ungrounded_claims(report: DraftReport, known_chunk_ids: set[str]) -> list[str]:
    """Return the text of claims that cite no evidence or unknown evidence chunks."""
    ungrounded = []
    for claim in report.claims:
        if not claim.supporting_chunk_ids:
            ungrounded.append(claim.text)
        elif not all(chunk_id in known_chunk_ids for chunk_id in claim.supporting_chunk_ids):
            ungrounded.append(claim.text)
    return ungrounded


def require_grounded_report(report: DraftReport, known_chunk_ids: set[str]) -> None:
    ungrounded = find_ungrounded_claims(report, known_chunk_ids)
    if ungrounded:
        raise ValueError(
            "Report contains claims without valid supporting evidence: " + "; ".join(ungrounded)
        )
