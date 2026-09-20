from research_mesh.domain.models import ResearchRequest, ResearchRun, RunEvent, RunStatus
from research_mesh.memory.sqlite import SQLiteRepository


def test_run_round_trips_through_sqlite() -> None:
    repository = SQLiteRepository(":memory:")
    run = ResearchRun(request=ResearchRequest(question="How does solar power work?"))

    repository.save_run(run)
    repository.add_event(RunEvent(run_id=run.id, event_type="run.created", message="Run queued"))

    restored = repository.get_run(str(run.id))
    assert restored == run


def test_run_status_update_is_persisted() -> None:
    repository = SQLiteRepository(":memory:")
    run = ResearchRun(request=ResearchRequest(question="What is retrieval augmented generation?"))
    repository.save_run(run)

    repository.update_status(str(run.id), RunStatus.RUNNING)

    restored = repository.get_run(str(run.id))
    assert restored is not None
    assert restored.status is RunStatus.RUNNING
    assert restored.updated_at.tzinfo is not None
