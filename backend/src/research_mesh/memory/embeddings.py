"""Factories for embedding functions backed by a local Ollama server."""

from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBEDDING_MODEL = "bge-m3"


def create_ollama_embedding_function(
    *,
    url: str = DEFAULT_OLLAMA_URL,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    timeout: int = 60,
) -> OllamaEmbeddingFunction:
    """Build an embedding function backed by a local Ollama server.

    Constructing this does not make any network call; embeddings are only
    requested when the returned function is actually invoked.
    """
    return OllamaEmbeddingFunction(url=url, model_name=model_name, timeout=timeout)
