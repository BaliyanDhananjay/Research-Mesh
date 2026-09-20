from research_mesh.memory.embeddings import create_ollama_embedding_function


def test_create_ollama_embedding_function_uses_expected_defaults() -> None:
    embedding_function = create_ollama_embedding_function()

    assert embedding_function.name() == "ollama"
    config = embedding_function.get_config()
    assert config["url"] == "http://localhost:11434"
    assert config["model_name"] == "bge-m3"


def test_create_ollama_embedding_function_accepts_overrides() -> None:
    embedding_function = create_ollama_embedding_function(
        url="http://localhost:9999", model_name="nomic-embed-text", timeout=30
    )

    config = embedding_function.get_config()
    assert config["url"] == "http://localhost:9999"
    assert config["model_name"] == "nomic-embed-text"
    assert config["timeout"] == 30
