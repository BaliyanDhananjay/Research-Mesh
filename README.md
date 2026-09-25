# Research Mesh

Research Mesh is a local-first, citation-backed multi-agent research assistant.

## Repository layout

- `backend/` — Python service: domain models, retrieval, persistence, orchestration, and the
  FastAPI API. Self-contained: its own `pyproject.toml`, `.venv`, and `.env.example`.
- `backend/src/research_mesh/domain/` — typed application contracts
- `backend/src/research_mesh/memory/` — SQLite persistence and ChromaDB vector store
- `backend/src/research_mesh/retrieval/` — search, fetching, extraction, and evidence preparation
- `backend/src/research_mesh/orchestration/` — research run lifecycle and agent coordination
- `backend/src/research_mesh/agents/` — structured agent contracts and claim validation
- `backend/src/research_mesh/api/` — FastAPI service exposing the pipeline over HTTP
- `backend/tests/` — backend unit and integration tests
- `frontend/` — React + TypeScript dashboard (Vite); talks to the backend over HTTP only
- `docs/` — architecture, setup, and evaluation documentation as the project grows

## Running the backend API

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
py -m uvicorn research_mesh.api.app:app --reload
```

Requires a local Ollama server (chat + embedding models) and a SearXNG instance configured
via the environment variables in `backend/.env.example`.

```powershell
py -m pytest              # tests
py -m ruff check src tests
py -m ruff format --check src tests
py -m mypy src
```

The backend is intentionally offline-first during development. Retrieval and local model
inference use replaceable interfaces.

## Running the frontend dashboard

```powershell
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. Copy `frontend/.env.example` to `frontend/.env` and set
`VITE_API_BASE_URL` if the backend isn't running at `http://localhost:8000`.

```powershell
npm run build   # production build
npm test        # Vitest + React Testing Library
npm run lint    # Oxlint
```

