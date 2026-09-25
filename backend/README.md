# Research Mesh Backend

Python backend: domain models, retrieval, persistence, orchestration, and the FastAPI service.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
```

## Run

```powershell
py -m uvicorn research_mesh.api.app:app --reload
```

## Test

```powershell
py -m pytest -q
py -m ruff check src tests
py -m ruff format --check src tests
py -m mypy src
```

See the root `README.md` for the full project overview, including the frontend.
