"""Thin client for local text generation via a running Ollama server."""

from dataclasses import dataclass

from ollama import Client

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_CHAT_MODEL = "qwen2.5:7b"


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class OllamaChatClient:
    """Wraps a local Ollama server for chat-style text generation."""

    def __init__(
        self,
        *,
        url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_CHAT_MODEL,
        timeout: float = 120.0,
        client: Client | None = None,
    ) -> None:
        self.model = model
        self._client = client or Client(host=url, timeout=timeout)

    def complete(self, messages: list[ChatMessage], *, as_json: bool = False) -> str:
        if not messages:
            raise ValueError("At least one message is required")
        response = self._client.chat(
            model=self.model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            format="json" if as_json else "",
        )
        content = response.message.content
        if not content:
            raise ValueError("Ollama returned an empty response")
        return content

    def is_available(self) -> bool:
        """Check whether the configured Ollama server is reachable."""
        try:
            self._client.list()
        except Exception:
            return False
        return True
