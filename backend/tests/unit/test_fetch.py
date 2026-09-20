import httpx
import pytest
from research_mesh.retrieval.fetch import SourceFetcher


def test_fetcher_returns_bounded_html_text() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<p>Evidence</p>",
        )

    fetcher = SourceFetcher(client=httpx.Client(transport=httpx.MockTransport(handler)))

    document = fetcher.fetch("https://example.com/article")

    assert document.content_type == "text/html"
    assert document.content == "<p>Evidence</p>"


@pytest.mark.parametrize(
    "headers, body",
    [
        ({"content-type": "application/pdf"}, b"%PDF"),
        ({"content-type": "text/plain"}, b"x" * 1_025),
    ],
)
def test_fetcher_rejects_unsupported_or_oversized_content(
    headers: dict[str, str], body: bytes
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers=headers, content=body)

    fetcher = SourceFetcher(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_bytes=1_024,
    )

    with pytest.raises(ValueError):
        fetcher.fetch("https://example.com/article")
