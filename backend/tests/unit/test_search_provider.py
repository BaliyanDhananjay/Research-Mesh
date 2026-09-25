import httpx
import pytest

from research_mesh.retrieval.search import SearXNGSearchProvider


def test_search_provider_maps_valid_results_and_skips_invalid_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["format"] == "json"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://example.com/article",
                        "title": "Useful article",
                        "content": "Relevant evidence",
                    },
                    {"title": "Missing URL"},
                    {"url": "file:///unsafe"},
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = SearXNGSearchProvider("https://search.example/search", client=client)

    results = provider.search("renewable energy", limit=5)

    assert len(results) == 1
    assert str(results[0].url) == "https://example.com/article"


def test_search_provider_rejects_invalid_query_and_limit() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})))
    provider = SearXNGSearchProvider("https://search.example/search", client=client)

    with pytest.raises(ValueError):
        provider.search("   ")
    with pytest.raises(ValueError):
        provider.search("query", limit=0)
