"""Environment-driven configuration and service construction for the API."""

import os
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request

from research_mesh.memory.embeddings import create_ollama_embedding_function
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.memory.vector_store import ChromaVectorStore
from research_mesh.orchestration.jobs import RunJobManager
from research_mesh.orchestration.model_client import OllamaChatClient
from research_mesh.orchestration.runner import ResearchOrchestrator
from research_mesh.retrieval.fetch import SourceFetcher
from research_mesh.retrieval.search import SearXNGSearchProvider


def get_database_path() -> str:
    return os.environ.get("RESEARCH_MESH_DATABASE_PATH", "data/research_mesh.sqlite3")


def build_orchestrator() -> ResearchOrchestrator:
    """Construct a fully wired orchestrator from environment configuration.

    Each call opens its own SQLite connection and Chroma client, so an
    instance built by this factory is safe to hand off to a single
    background thread.
    """
    ollama_url = os.environ.get("RESEARCH_MESH_OLLAMA_BASE_URL", "http://localhost:11434")
    chat_model = os.environ.get("RESEARCH_MESH_OLLAMA_MODEL", "qwen2.5:7b")
    embedding_model = os.environ.get("RESEARCH_MESH_EMBEDDING_MODEL", "bge-m3")
    search_url = os.environ.get("RESEARCH_MESH_SEARCH_URL", "http://localhost:8080/search")
    database_path = get_database_path()

    repository = SQLiteRepository(database_path)
    vector_store = ChromaVectorStore(
        embedding_function=create_ollama_embedding_function(
            url=ollama_url, model_name=embedding_model
        ),
        persist_directory=str(Path(database_path).parent / "chroma"),
    )
    return ResearchOrchestrator(
        repository=repository,
        vector_store=vector_store,
        search_provider=SearXNGSearchProvider(search_url),
        fetcher=SourceFetcher(),
        chat_client=OllamaChatClient(url=ollama_url, model=chat_model),
    )


def get_orchestrator(request: Request) -> ResearchOrchestrator:
    factory = request.app.state.orchestrator_factory
    orchestrator: ResearchOrchestrator = factory()
    return orchestrator


def get_job_manager(request: Request) -> RunJobManager:
    job_manager: RunJobManager = request.app.state.job_manager
    return job_manager


def get_repository() -> Iterator[SQLiteRepository]:
    repository = SQLiteRepository(get_database_path())
    try:
        yield repository
    finally:
        repository.close()
