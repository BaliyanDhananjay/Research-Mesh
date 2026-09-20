import io

import pytest
from pypdf import PdfWriter
from research_mesh.retrieval.extraction import (
    canonicalize_url,
    chunk_text,
    content_hash,
    deduplicate_candidates,
    extract_pdf_text,
    extract_text,
)
from research_mesh.retrieval.models import SourceCandidate


def test_html_extraction_ignores_code_and_scripts() -> None:
    html = (
        "<article><h1>Research title</h1><p>Useful evidence.</p><script>secret()</script></article>"
    )

    assert extract_text(html) == "Research title Useful evidence."


def test_url_and_content_normalization_are_stable() -> None:
    first = "HTTPS://Example.com/article?utm_source=news&b=2#a"
    second = "https://example.com/article?b=2&utm_source=news"

    assert canonicalize_url(first) == canonicalize_url(second)
    assert content_hash(" same   evidence ") == content_hash("same evidence")


def test_duplicate_search_results_are_removed() -> None:
    candidates = [
        SourceCandidate(url="https://example.com/article?utm_source=one", title="First"),
        SourceCandidate(url="https://example.com/article?utm_source=two", title="Second"),
        SourceCandidate(url="https://example.org/other", title="Other"),
    ]

    unique = deduplicate_candidates(candidates)

    assert [candidate.title for candidate in unique] == ["First", "Other"]


def test_chunking_respects_maximum_size() -> None:
    chunks = chunk_text("word " * 300, max_chars=100)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert all(chunk for chunk in chunks)


def test_pdf_extraction_succeeds_for_a_valid_pdf() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    assert extract_pdf_text(buffer.getvalue()) == ""


def test_pdf_extraction_rejects_invalid_bytes() -> None:
    with pytest.raises(ValueError):
        extract_pdf_text(b"not a pdf")


def test_pdf_extraction_rejects_empty_bytes() -> None:
    with pytest.raises(ValueError):
        extract_pdf_text(b"")
