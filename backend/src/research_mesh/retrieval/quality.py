"""Transparent, deterministic source ranking for the first retrieval phase."""

from research_mesh.retrieval.models import SourceCandidate

TRUSTED_SUFFIXES = (".gov", ".edu", ".ac.uk")
TRUSTED_DOMAINS = {"pubmed.ncbi.nlm.nih.gov", "arxiv.org", "who.int"}


def score_source(candidate: SourceCandidate) -> float:
    """Return a bounded score; this ranks sources but never proves correctness."""
    domain = (candidate.domain or candidate.url.host or "").lower()
    score = 0.25
    if domain in TRUSTED_DOMAINS or domain.endswith(TRUSTED_SUFFIXES):
        score += 0.35
    if candidate.is_primary_source:
        score += 0.15
    if candidate.title.strip():
        score += 0.10
    if candidate.snippet.strip():
        score += 0.10
    if candidate.published_year is not None:
        score += 0.05
    return min(score, 1.0)
