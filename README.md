# Research Mesh

Research Mesh is a local-first, citation-backed multi-agent research assistant.

## Repository layout

- `backend/src/research_mesh/domain/` — typed application contracts
- `backend/src/research_mesh/memory/` — SQLite persistence
- `backend/src/research_mesh/retrieval/` — search, fetching, extraction, and evidence preparation
- `backend/src/research_mesh/orchestration/` — research run lifecycle and agent coordination
- `backend/tests/` — backend unit and integration tests
- `frontend/` — the future Streamlit dashboard; presentation-only, no search, model, or
  persistence logic
- `docs/` — architecture, setup, and evaluation documentation as the project grows

## Development

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
py -m pytest
```

The backend is intentionally offline-first during development. Retrieval and local model
inference use replaceable interfaces, while the dashboard will live under `frontend/`.
