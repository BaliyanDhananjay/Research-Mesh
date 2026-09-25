import pytest

from research_mesh.retrieval.models import SourceCandidate
from research_mesh.retrieval.quality import score_source
from research_mesh.retrieval.safety import validate_fetch_url


def test_trusted_primary_source_scores_above_generic_result() -> None:
    trusted = SourceCandidate(
        url="https://pubmed.ncbi.nlm.nih.gov/123",
        title="A clinical study",
        snippet="Study findings",
        source_type="academic",
        is_primary_source=True,
        published_year=2025,
    )
    generic = SourceCandidate(url="https://example.com/result")

    assert score_source(trusted) > score_source(generic)
    assert 0.0 <= score_source(trusted) <= 1.0


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://localhost:8080/health",
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
    ],
)
def test_private_or_unsafe_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        validate_fetch_url(url)


def test_public_https_url_is_allowed() -> None:
    validate_fetch_url("https://example.com/research")
