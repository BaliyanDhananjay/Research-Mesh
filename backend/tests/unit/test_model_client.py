import httpx
import pytest
from ollama import Client

from research_mesh.orchestration.model_client import ChatMessage, OllamaChatClient


def test_complete_returns_assistant_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "qwen2.5:7b",
                "created_at": "2026-09-20T00:00:00Z",
                "message": {"role": "assistant", "content": "Hello from the model"},
                "done": True,
            },
        )

    client = Client(host="http://ollama.local", transport=httpx.MockTransport(handler))
    chat_client = OllamaChatClient(client=client)

    reply = chat_client.complete([ChatMessage(role="user", content="Hi")])

    assert reply == "Hello from the model"


def test_complete_rejects_empty_messages() -> None:
    chat_client = OllamaChatClient(client=Client(host="http://ollama.local"))

    with pytest.raises(ValueError):
        chat_client.complete([])


def test_is_available_returns_false_when_server_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = Client(host="http://ollama.local", transport=httpx.MockTransport(handler))
    chat_client = OllamaChatClient(client=client)

    assert chat_client.is_available() is False
