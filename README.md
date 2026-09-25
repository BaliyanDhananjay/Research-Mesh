# Research Mesh

Research Mesh is a local-first, citation-backed multi-agent research assistant.

## Repository layout

- `backend/src/research_mesh/domain/` — typed application contracts
- `backend/src/research_mesh/memory/` — SQLite persistence and ChromaDB vector store
- `backend/src/research_mesh/retrieval/` — search, fetching, extraction, and evidence preparation
- `backend/src/research_mesh/orchestration/` — research run lifecycle and agent coordination
- `backend/src/research_mesh/agents/` — structured agent contracts and claim validation
- `backend/src/research_mesh/api/` — FastAPI service exposing the pipeline over HTTP
- `backend/tests/` — backend unit and integration tests
- `frontend/` — Streamlit dashboard; presentation-only, talks to the backend over HTTP
- `docs/` — architecture, setup, and evaluation documentation as the project grows

## Development

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
py -m pytest
```

The backend is intentionally offline-first during development. Retrieval and local model
inference use replaceable interfaces.

## Running the backend API

```powershell
py -m uvicorn research_mesh.api.app:app --reload
```

Requires a local Ollama server (chat + embedding models) and a SearXNG instance configured
via the environment variables in `.env.example`.

## Running the frontend dashboard

```powershell
cd frontend
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Set `RESEARCH_MESH_API_BASE_URL` if the backend isn't running at `http://localhost:8000`.

