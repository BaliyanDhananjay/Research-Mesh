import pytest

from research_mesh.domain.models import RunStatus
from research_mesh.orchestration.state import transition_status


def test_run_can_progress_from_queued_to_completed() -> None:
    status = transition_status(RunStatus.QUEUED, RunStatus.RUNNING)
    status = transition_status(status, RunStatus.COMPLETED)

    assert status is RunStatus.COMPLETED


def test_completed_run_cannot_be_reopened() -> None:
    with pytest.raises(ValueError, match="Invalid run transition"):
        transition_status(RunStatus.COMPLETED, RunStatus.RUNNING)


def test_failed_or_cancelled_runs_can_be_queued_for_retry() -> None:
    assert transition_status(RunStatus.FAILED, RunStatus.QUEUED) is RunStatus.QUEUED
    assert transition_status(RunStatus.CANCELLED, RunStatus.QUEUED) is RunStatus.QUEUED
