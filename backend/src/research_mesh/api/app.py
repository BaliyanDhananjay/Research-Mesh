"""FastAPI service exposing the research orchestration pipeline over HTTP."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException

from research_mesh.api.dependencies import (
    build_orchestrator,
    get_job_manager,
    get_orchestrator,
    get_repository,
)
from research_mesh.domain.models import (
    Report,
    ResearchRequest,
    ResearchRun,
    RunEvent,
    SourceDocument,
)
from research_mesh.memory.sqlite import SQLiteRepository
from research_mesh.orchestration.jobs import RunJobManager
from research_mesh.orchestration.runner import ResearchOrchestrator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.orchestrator_factory = build_orchestrator
    app.state.job_manager = RunJobManager()
    yield
    app.state.job_manager.shutdown()


app = FastAPI(title="Research Mesh API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", response_model=ResearchRun, status_code=202)
def create_run(
    request: ResearchRequest,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator),
    job_manager: RunJobManager = Depends(get_job_manager),
) -> ResearchRun:
    run = orchestrator.create_run(request)
    # Snapshot before handing off: execute() mutates `run` in place on another thread.
    response_run = run.model_copy()
    job_manager.submit(run.id, lambda: orchestrator.execute(run))
    return response_run


@app.get("/runs/{run_id}", response_model=ResearchRun)
def get_run(run_id: UUID, repository: SQLiteRepository = Depends(get_repository)) -> ResearchRun:
    run = repository.get_run(str(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/runs/{run_id}/events", response_model=list[RunEvent])
def list_run_events(
    run_id: UUID, repository: SQLiteRepository = Depends(get_repository)
) -> list[RunEvent]:
    if repository.get_run(str(run_id)) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return repository.list_events_for_run(str(run_id))


@app.get("/runs/{run_id}/sources", response_model=list[SourceDocument])
def list_run_sources(
    run_id: UUID, repository: SQLiteRepository = Depends(get_repository)
) -> list[SourceDocument]:
    if repository.get_run(str(run_id)) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return repository.list_sources_for_run(str(run_id))


@app.get("/runs/{run_id}/report", response_model=Report)
def get_run_report(run_id: UUID, repository: SQLiteRepository = Depends(get_repository)) -> Report:
    if repository.get_run(str(run_id)) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    report = repository.get_report_for_run(str(run_id))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not available yet")
    return report
